from typing import Generic, Optional, TypeVar
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar('T')


class AppResponse(BaseModel, Generic[T]):
    success: bool = Field(description="Is operation success", default=True)
    status_code: int = Field(description="status code", default=200)
    message: str = Field(description="Message back to client", default="done")
    
    data: Optional[T] = None
    
    model_config = ConfigDict(
        alias_generator=AliasGenerator(to_camel),
        populate_by_name=True,
    )
    
        
