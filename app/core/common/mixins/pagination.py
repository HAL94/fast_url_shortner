
import enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, ColumnElement, DateTime, asc, desc
from sqlalchemy.sql.sqltypes import Integer, Float
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.db.database import Base
from app.core.exceptions import BadRequestException


class LogicalOperator(enum.Enum):
    EQ = '='
    LTE = '<='
    LT = '<'
    GTE = '>='
    GT = '>'
    NOT = '!='


class InvalidOperator(Exception):
    pass

class InvalidDatetimeValue(Exception):
    def __init__(self, message = 'Type of field is datetime, value has to be in isoformat'):
        super().__init__(message)
        self.message = message

class FieldOperation:
    @classmethod
    def determine_operator(cls, field_str: str) -> LogicalOperator:

        if LogicalOperator.GTE.value in field_str:
            return LogicalOperator.GTE

        if LogicalOperator.GT.value in field_str:
            return LogicalOperator.GT

        if LogicalOperator.LTE.value in field_str:
            return LogicalOperator.LTE

        if LogicalOperator.LT.value in field_str:
            return LogicalOperator.LT

        if LogicalOperator.NOT.value in field_str:
            return LogicalOperator.NOT

        if LogicalOperator.EQ.value in field_str:
            return LogicalOperator.EQ

        raise InvalidOperator

    @classmethod
    def get_sql_expression(cls, column: str, operator: LogicalOperator, column_value: Any) -> list[ColumnElement]:
        if operator is LogicalOperator.GTE:
            return [column >= column_value]
        if operator is LogicalOperator.GT:
            return [column > column_value]
        if operator is LogicalOperator.LTE:
            return [column <= column_value]
        if operator is LogicalOperator.LT:
            return [column < column_value]
        if operator is LogicalOperator.NOT:
            return [column != column_value]
        if operator is LogicalOperator.EQ:
            return [column == column_value]

        raise ValueError("No suppoerted oeprations were determined")


class PaginationParser:

    @classmethod
    def split_and_clean_fields(cls, fields: Optional[str] = None) -> list[str]:
        if not fields:
            return []
        return [field.strip() for field in fields.split(',')]

    @classmethod
    def validate_field(cls, field: str, allowed_fields: list[str], error_message: str) -> None:
        """Validates if a field is in the allowed list."""
        # print(f"validatin if {field} exist in {allowed_fields}")
        if field not in allowed_fields:
            raise ValueError(error_message.format(
                field=field, allowed_fields=allowed_fields))

    @classmethod
    def convert_value(cls, *, value: Any, column_type: Any, field_name: str):
        """
        Convert value to appropriate type based on column type.

        :param value: String value to convert
        :param column_type: SQLAlchemy column type
        :return: Converted value
        """
        try:
            if isinstance(column_type, Integer):
                return int(value)
            if isinstance(column_type, Float):
                return float(value)
            if isinstance(column_type, Boolean):
                return bool(value)
            if isinstance(column_type, DateTime):                
                from datetime import datetime
                try:
                    return datetime.fromisoformat(value)
                except Exception:
                    raise InvalidDatetimeValue(message = f"Expected type of '{field_name}' is '{str(column_type).lower()}', could not parse the value '{value}'")
            return value
        except InvalidDatetimeValue as e:
            raise BadRequestException(detail=str(e))
        except Exception:
            raise ValueError(
                f"Type of field '{field_name}' is '{str(column_type).lower()}' but value passed is: '{type(value).__name__}'")


class PaginationSortParser(PaginationParser):
    def _process_sort_fields(self, model: Base) -> list[InstrumentedAttribute]:
        """
        Process and validate sort fields.

        :param model: SQLAlchemy model class
        :return: List of sort expressions
        """
        print(f"sort_by is: {self.sort_by}")
        sort_fields = self.split_and_clean_fields(self.sort_by)
        sort_by = []

        for field in sort_fields:
            if not field:
                continue

            clean_field = field.lstrip('-')
            is_descending = field.startswith('-')

            try:
                column = getattr(model, clean_field)
                sort_expr = desc(column) if is_descending else asc(column)
                sort_by.append(sort_expr)
            except Exception as e:
                print(f"Invalid sort field: {clean_field}")

        return sort_by


class PaginationFilterParser(PaginationParser):
    def _process_filter_fields(self, model: Base) -> list[ColumnElement]:
        """
        Process and validate filter fields with type conversion.

        :param model: SQLAlchemy model class
        :return: List of filter expressions
        """
        filter_fields = self.split_and_clean_fields(self.filter_by)
        filter_by = []

        for pair in filter_fields:
            if not pair:
                continue

            operator: LogicalOperator = None
            try:

                operator = FieldOperation.determine_operator(pair)

                key, value = pair.split(operator.value, 1)

                column = getattr(model, key)

                column_type = column.type

                converted_value = self.convert_value(
                    value=value, column_type=column_type, field_name=key)

                sql_expr = FieldOperation.get_sql_expression(
                    column=column, operator=operator, column_value=converted_value)

                print(f"sql_expr: {sql_expr}")

                filter_by.extend(sql_expr)
            except InvalidOperator:
                print(f"Invalid oeprator passed")
            except ValueError as e:
                print(f"Invalid filter: {pair} {operator}")
                raise BadRequestException(detail=str(e)) from e

        return filter_by


class PaginationMixin(BaseModel, PaginationFilterParser, PaginationSortParser):
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    sort_by: Optional[str] = None
    filter_by: Optional[str] = None

    def convert_to_model(self, model: Base):
        sort_by = self._process_sort_fields(model)
        filter_by = self._process_filter_fields(model)
        return sort_by, filter_by

    @classmethod
    def create_pagination_mixin(cls, sortable_fields: list[str] = [], filterable_fields: list[str] = []):
        class ValidatedPaginationMixin(cls):
            @field_validator('sort_by')
            def validate_sort_fields(cls, v):
                if not v:
                    return v

                sort_fields = cls.split_and_clean_fields(v)

                for field in sort_fields:
                    clean_field = field.lstrip('-')

                    error_message = "Sorting not allowed on field '{field}'. Allowed fields are {allowed_fields}"

                    cls.validate_field(field=clean_field, allowed_fields=sortable_fields,
                                       error_message=error_message)

                return v

            @field_validator('filter_by')
            def validate_filter_fields(cls, v):
                if not v:
                    return v

                filter_pairs = cls.split_and_clean_fields(v)

                for pair in filter_pairs:
                    field = None

                    try:
                        operator: LogicalOperator = FieldOperation.determine_operator(
                            pair)
                        field, _ = pair.split(operator.value, 1)

                    except Exception:
                        raise ValueError(f"Invalid filter format. Passed field is '{pair}'."
                                         " Use 'field:value' format")

                    cls.validate_field(field=field, allowed_fields=filterable_fields,
                                       error_message="Filtering not allowed on field '{field}'. Allowed fields are {allowed_fields}")
                return v

        return ValidatedPaginationMixin
