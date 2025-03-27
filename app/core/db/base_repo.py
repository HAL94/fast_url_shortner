

from typing import Any, ClassVar, Generic, Optional, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, delete, insert, select, update
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql.elements import ColumnElement

from app.core.db.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.exceptions import BadRequestException, NotFoundException

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

    @property
    def _dbmodel(self) -> DbModel:
        return self.__dbmodel__

    async def create(self, data: BaseModel, return_model: Optional[BaseModel | PydanticModel] = None):
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
            insert(self._dbmodel).values(
                data.model_dump(exclude_none=True)).returning(self._dbmodel)
        )
        await session.commit()

        if not return_model:
            return_model = self._model

        return return_model(**created_db_model.dict())

    async def upsert_many(self,
                          data: list[BaseModel],
                          index_elements: list[InstrumentedAttribute |
                                               str] | None = None,
                          return_model: Optional[list[BaseModel | PydanticModel]] = None):
        """
        Performs a bulk upsert operation on the database table.

        This function inserts or updates multiple rows in the database based on the provided data.
        If a row with the specified index elements already exists, it updates the row; otherwise, it inserts a new row.

        Args:
            data: A list of BaseModel instances representing the data to be upserted.
            index_elements: A list of InstrumentedAttribute or string column names used to determine conflicts.
                            Defaults to the primary key 'id' if not provided.
            return_model: An optional BaseModel instance to use for returning the results.
                        Defaults to the model associated with the repository if not provided.

        Returns:
            A list of PydanticModel instances representing the upserted or updated rows.

        Example:
            >>> await repository.upsert_many(
            ...     data=[MyModel(id=1, name='Updated Name'), MyModel(id=2, name='New Name')],
            ...     index_elements=['id'],
            ...     return_model=MyPydanticModel
            ... )
            [MyPydanticModel(...), MyPydanticModel(...)]
        """
        try:

            if not index_elements:
                index_elements = [self._dbmodel.id]

            index_elements = [str(col).split('.')[1] if isinstance(
                col, InstrumentedAttribute) else str(col) for col in index_elements]

            model_columns = self._dbmodel.columns()

            session = self.session

            data_values = [item.model_dump() for item in data]
            data_model_fields = data[0].model_fields

            data_keys = set(data_model_fields.keys())
            index_keys = set(index_elements)

            # if all keys in data match with index_elements, then the operation is invalid
            # because there are not distinctions that could be used for the on conflict clause.
            if len(data_keys - index_keys) == 0:
                raise ValueError(
                    f"Index elements match all model fields, upsert is invalid.")

            #  if no key in index_elements exists in data, then the operation is invalid
            missing_keys = index_keys - data_keys
            if missing_keys:
                raise ValueError(
                    f"Data passed must include the indexed_elements to handle conflicts. Missing: {missing_keys}")

            stmt = pg_insert(self._dbmodel).values(data_values)

            updated_columns = {
                key: getattr(stmt.excluded, key)
                # Use the first data object's keys
                for key in data_values[0].keys()
                if key not in index_elements  # Ensure index elements are not updated
            }

            if 'updated_at' in model_columns:
                updated_columns['updated_at'] = func.now()

            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=updated_columns
            )

            updated_or_created_data = await session.scalars(
                stmt.returning(self._dbmodel), execution_options={"populate_existing": True}
            )

            await session.commit()

            return_model = return_model or self._model

            result = updated_or_created_data.all()

            return [return_model(**item.dict()) for item in result]
        except ProgrammingError:
            raise ValueError(
                "there is no unique or exclusion constraint matching the ON CONFLICT specification. Background on this error at: https://sqlalche.me/e/20/f405)")

    async def get_many(self,
                       page: int,
                       size: int,
                       where_clause: list[ColumnElement[bool]] = [],
                       order_clause: list[InstrumentedAttribute] = [],
                       return_model: Optional[BaseModel | PydanticModel] = None):

        session = self.session        

        stmt = select(self._dbmodel).where(
            *where_clause).order_by(*order_clause).offset((page-1)*size).limit(size)

        result = await session.scalars(stmt)

        total_count = await session.scalar(select(func.count()).select_from(select(self._dbmodel).where(*where_clause).subquery()))        

        # print(f"total_count: {total_count}")

        return_model = return_model or self._model

        result = {
            "data": [item.dict() for item in result],
            "total_count": total_count
        }

        return return_model(**result)

    async def get_one(self,
                      val: Any,
                      field: InstrumentedAttribute | None = None,
                      where_clause: list[ColumnElement[bool]] = None,
                      return_model: Optional[BaseModel | PydanticModel] = None):
        """
        Retrieves a single record from the database matching the given criteria.

        Args:
            val: The value to search for.
            field: The InstrumentedAttribute representing the column to search in. Defaults to the model's primary key.
            where_clause: An optional list of additional SQLAlchemy where clauses to apply.
            return_model: An optional BaseModel or PydanticModel to use for returning the result. Defaults to the repository's model.

        Returns:
            A PydanticModel instance representing the found record.

        Raises:
            NotFoundException: If no matching record is found.
        """
        session = self.session

        if field is None:
            field = self._dbmodel.id

        where_cond: list = [getattr(self._dbmodel, field) == val]

        if where_clause:
            where_cond.extend(where_clause)

        result = await session.scalar(
            select(self._dbmodel).where(*where_cond)
        )

        if result is None:
            raise NotFoundException

        return_model = return_model or self._model

        return return_model(**result.dict())

    async def update_one(self, data: BaseModel,
                         where_clause: list[ColumnElement[bool]] = None,
                         return_model: Optional[BaseModel | PydanticModel] = None, ):
        """
        Updates a single record in the database matching the given criteria.

        Args:
            data: A BaseModel instance containing the updated data.
            where_clause: A list of SQLAlchemy where clauses to identify the record to update.
            return_model: An optional BaseModel or PydanticModel to use for returning the result. Defaults to the repository's model.

        Returns:
            A PydanticModel instance representing the updated record.

        Raises:
            ValueError: If no where_clause is provided.
            NotFoundException: If no matching record is found.
        """
        session = self.session

        if not where_clause:
            raise ValueError('must pass where_clause')

        updated_db_model = await session.scalar(
            update(self._dbmodel).values(
                data.model_dump(exclude_none=True))
            .filter(*where_clause)
            .returning(self._dbmodel)
        )

        await session.commit()

        if updated_db_model is None:
            raise NotFoundException

        if not return_model:
            return_model = self._model

        return return_model(**updated_db_model.dict())

    async def delete_one(self, val: Any, field: InstrumentedAttribute | None = None, where_clause: list[ColumnElement[bool]] = None,
                         return_model: Optional[BaseModel | PydanticModel] = None, ):
        """
        Deletes a single record from the database matching the given criteria.

        Args:
            val: The value to search for.
            field: The InstrumentedAttribute representing the column to search in. Defaults to the model's primary key.
            where_clause: An optional list of additional SQLAlchemy where clauses to apply.
            return_model: An optional BaseModel or PydanticModel to use for returning the deleted record. Defaults to the repository's model.

        Returns:
            A PydanticModel instance representing the deleted record.

        Raises:
            NotFoundException: If no matching record is found.
        """

        session = self.session

        if field is None:
            field = self._dbmodel.id

        where_cond: list = [getattr(self._dbmodel, field) == val]

        if where_clause:
            where_cond.extend(where_clause)

        deleted_db_model = await session.scalar(
            delete(self._dbmodel)
            .filter(*where_cond)
            .returning(self._dbmodel)
        )

        await session.commit()

        if not deleted_db_model:
            raise NotFoundException

        if not return_model:
            return_model = self._model

        return return_model(**deleted_db_model.dict())

    async def delete_many(self,
                          where_clause: list[ColumnElement[bool]],
                          return_model: Optional[BaseModel | PydanticModel] = None):
        """
        Deletes multiple records from the database matching the given criteria.

        Args:
            where_clause: A list of SQLAlchemy where clauses to identify the records to delete.
            return_model: An optional BaseModel or PydanticModel to use for returning the deleted records. Defaults to the repository's model.

        Returns:
            A list of PydanticModel instances representing the deleted records.

        Raises:
            ValueError: If no where_clause is provided.
        """
        session = self.session

        if not where_clause:
            raise ValueError("'where_cluse' must be passed")

        deleted_model_records = await session.scalars(
            delete(self._dbmodel).where(*where_clause).returning(self._dbmodel)
        )

        await session.commit()

        result = deleted_model_records.all()

        print(f"deleted_records: {result} at where_clause: {where_clause}")

        if not return_model:
            return_model = self._model

        return [return_model(**item.dict()) for item in result]

    async def update_many(
        self,
        data: list[BaseModel],
        field: Any = 'id',
        return_model: Optional[BaseModel | PydanticModel] = None,
    ) -> list[BaseModel | PydanticModel]:

        if not all(field in item.model_fields for item in data):
            raise ValueError(
                f"Each item in 'data' must contain an '{field}' key.")

        session: AsyncSession = self.session

        data = [item.model_dump(exclude_none=True) for item in data]

        # unlike a single record update, a bulk update does not support RETURNING
        # it is best to update with `executemany` which receives a parameter sets
        await session.execute(
            update(self._dbmodel), data
        )

        await session.commit()

        result = await session.scalars(
            select(self._dbmodel).filter(
                self._dbmodel.id.in_([item.get('id') for item in data]))
        )

        return_model = return_model or self._model

        return [return_model(**item.dict()) for item in result.all()]
