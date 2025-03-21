

from typing import Any, ClassVar, Generic, Optional, TypeVar
from asyncpg import UniqueViolationError
from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update
from sqlalchemy.sql.elements import ColumnElement

from app.core.db.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.exceptions import AlreadyExistsException, NotFoundException, ServerFailException

DbModel = TypeVar('T', bound=Base)  # type: ignore
PydanticModel = TypeVar('M', bound=BaseModel)


class BaseRepo(Generic[DbModel, PydanticModel]):
    __dbmodel__: ClassVar[DbModel]
    __model__: ClassVar[PydanticModel]

    def __init__(self, session: AsyncSession):
        self.session = session
    
    @property
    def _model(self) -> PydanticModel:
        return self.__model__

    async def create(self, data: BaseModel, return_model: Optional[BaseModel | PydanticModel] = PydanticModel):
        """
        Accepts a Pydantic model as data, creates a new record in the database, catches
        any integrity errors, and returns the record as pydantic model.

        Args:                
            data (BaseModel): Pydantic model

        Returns:
            created SQLAlchemy model
        """
        session = self.session
        created_db_model = await session.scalar(
            insert(self.__dbmodel__).values(
                data.model_dump(exclude_none=True)).returning(self.__dbmodel__)
        )
        await session.commit()
        return return_model(**created_db_model.dict())

    async def get_one_or_none(self,
                              val: Any,
                              field: InstrumentedAttribute | None = None,
                              where_clause: list[ColumnElement[bool]] = None,
                              return_model: Optional[BaseModel | PydanticModel] = None):

        session = self.session

        if field is None:
            field = self.__dbmodel__.id

        where_cond: list = [getattr(self.__dbmodel__, field) == val]

        if where_clause:
            where_cond.extend(where_clause)

        result = await session.scalar(
            select(self.__dbmodel__).where(*where_cond)
        )

        if result is None:
            raise NotFoundException        
        
        if not return_model:
            return_model = self._model
            
        return return_model(**result.dict())

    async def update_one(self, data: BaseModel,                         
                         where_clause: list[ColumnElement[bool]] = None,
                         return_model: Optional[BaseModel | PydanticModel] = None, ):

        session = self.session

        if not where_clause:
            raise ValueError('must pass where_clause')

        updated_db_model = await session.scalar(
            update(self.__dbmodel__).values(
                data.model_dump(exclude_none=True))
            .filter(*where_clause)
            .returning(self.__dbmodel__)
        )

        await session.commit()

        if updated_db_model is None:
            raise NotFoundException
        
        if not return_model:
            return_model = self._model
                    
        return return_model(**updated_db_model.dict())
        

    async def delete_one(self, val: Any, field: InstrumentedAttribute | None = None, where_clause: list[ColumnElement[bool]] = None,
                         return_model: Optional[BaseModel | PydanticModel] = PydanticModel, ):

        session = self.session

        if field is None:
            field = self.__dbmodel__.id

        where_cond: list = [getattr(self.__dbmodel__, field) == val]

        if where_clause:
            where_cond.extend(where_clause)

        deleted_db_model = await session.scalar(
            delete(self.__dbmodel__)
            .filter(*where_cond)
            .returning(self.__dbmodel__)
        )

        await session.commit()

        return return_model(**deleted_db_model.dict())
