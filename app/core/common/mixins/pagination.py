
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, ColumnElement, DateTime, asc, desc
from sqlalchemy.sql.sqltypes import Integer, Float
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.db.database import Base


class PaginationMixin(BaseModel):
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    # comma separated str, if string prefixed by '-' it is descending order, else it is asecnding: -short_code,created_at
    sort_by: Optional[str] = None
    # comma seperated str with key-value pairs: "short_code:G3HI8d,access_count:2"
    filter_by: Optional[str] = None

    def convert_to_model(self, model: Base):
        sort_by = self._process_sort_fields(model)
        filter_by = self._process_filter_fields(model)
        return sort_by, filter_by

    def _process_sort_fields(self, model: Base) -> list[InstrumentedAttribute]:
        """
        Process and validate sort fields.

        :param model: SQLAlchemy model class
        :return: List of sort expressions
        """
        sort_fields = self.sort_by.split(',') if self.sort_by else []
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

    def _process_filter_fields(self, model: Base) -> list[ColumnElement]:
        """
        Process and validate filter fields with type conversion.
        
        :param model: SQLAlchemy model class
        :return: List of filter expressions
        """
        filter_fields = self.filter_by.split(',') if self.filter_by else []

        filter_by = []

        for pair in filter_fields:
            if not pair:
                continue

            try:
                key, value = pair.split(':', 1)

                column = getattr(model, key)
                
                column_type = column.type

                converted_value = self._convert_value(value=value, column_type=column_type)

                filter_by.extend([column == converted_value])
            except Exception:
                print(f"Invalid filter: {pair}")

        return filter_by

    def _convert_value(self, *, value: Any, column_type: Any):
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
                return datetime(value)            
            return value
        except Exception:
            return value

    @classmethod
    def create_pagination_mixin(cls, sortable_fields: list[str] = [], filterable_fields: list[str] = []):
        class ValidatedPaginationMixin(cls):            
            @field_validator('sort_by')
            def validate_sort_fields(cls, v):
                if not v:
                    return v
                sort_fields = v.split(',')
                for field in sort_fields:
                    clean_field = field.lstrip('-')
                    if clean_field not in sortable_fields:
                        raise ValueError(
                            f"Sorting not allowed on field '{clean_field}'. Allowed fields are: {sortable_fields}")

                return v

            @field_validator('filter_by')
            def validate_filter_fields(cls, v):
                if not v:
                    return v

                filter_pairs = v.split(',')
                for pair in filter_pairs:
                    key = None
                                        
                    try:
                        key, _ = pair.split(':', 1)
                    except Exception:
                        raise ValueError(f"Invalid filter format. Passed field is '{pair}'."
                                         " Use 'field:value' format")
                    
                    if key not in filterable_fields:
                        raise ValueError(f"Filtering not allowed on field: '{key}'. "
                                            f"Allowed fields are: {filterable_fields}")
                return v

        return ValidatedPaginationMixin
