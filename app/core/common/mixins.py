
from typing import Optional

from pydantic import BaseModel, field_validator
from sqlalchemy import asc, desc
from sqlalchemy.sql.sqltypes import Integer, Float

from app.core.db.database import Base


class PaginationMixin(BaseModel):
    page: int
    size: int
    # comma separated str, if string prefixed by '-' it is descending order, else it is asecnding: -short_code,created_at
    sort_by: Optional[str] = None
    # comma seperated str with key-value pairs: "short_code:G3HI8d,access_count:2"
    filter_by: Optional[str] = None

    def convert_to_model(self, model: Base):
        sort_fields = self.sort_by.split(',') if self.sort_by else []
        filter_fields = self.filter_by.split(',') if self.filter_by else []
        sort_by = []
        filter_by = []

        for field in sort_fields:
            field_with_direction = desc(field[1:]) if field.startswith('-') else asc(field)
            sort_by.append(field_with_direction)

        for pair in filter_fields:
            key, value = pair.split(":")
            try:
                column_type = getattr(model, key).type
                
                if isinstance(column_type, Integer):
                    value = int(value)
                if isinstance(column_type, Float):
                    value = float(value)
                    
            except ValueError:
                pass
            
            filter_by.extend([getattr(model, key) == value])
        
        return sort_by, filter_by


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
                            f"Sorting not allowed on field {clean_field}. Allowed fields are: {sortable_fields}")

                return v

            @field_validator('filter_by')
            def validate_filter_fields(cls, v):
                if not v:
                    return v

                filter_pairs = v.split(',')
                for pair in filter_pairs:
                    try:
                        key, value = pair.split(':')
                        if key not in filterable_fields:
                            raise ValueError(f"Filtering not allowed on field: {key}. "
                                             f"Allowed fields are: {filterable_fields}")

                    except ValueError:
                        raise ValueError("Invalid filter format: {pair}."
                                         "Use 'field:value' format")
                return v

        return ValidatedPaginationMixin
