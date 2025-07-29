from typing import Type, TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Select, asc, desc, func, literal_column
from db.base_model import Base
from db.base_query_params import BaseQueryParams
from db.exception import handle_db_exceptions

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    @handle_db_exceptions(allow_return=True)
    async def get_one(self, db: AsyncSession, **filters) -> Optional[ModelType]:
        """Fetch one record."""
        stmt = select(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)

        result = await db.execute(stmt)
        return result.scalars().first()

    @handle_db_exceptions(allow_return=True, return_data=[])
    async def get_all(
        self,
        db: AsyncSession,
        query_params: Optional[BaseQueryParams] = BaseQueryParams(),
    ) -> List[ModelType]:
        """
        Fetch multiple records based on query parameters.

        Args:
            db (AsyncSession): The database session.
            query_params (QueryParams): optional structured query parameters.

        Returns:
            List[ModelType]: A list of matching records.
        """
        stmt = select(self.model)

        if query_params.filters:
            stmt = stmt.filter_by(**query_params.filters)

        if query_params.order_by:
            column = getattr(self.model, query_params.order_by, None)
            if column:
                stmt = stmt.order_by(
                    asc(column) if query_params.sort.lower() == "asc" else desc(column))

        if query_params.limit is not None:
            stmt = stmt.offset(query_params.offset).limit(query_params.limit)

        result = await db.execute(stmt)
        return result.scalars().all()


    @handle_db_exceptions(allow_return=True, return_data=[])
    async def group_by_sum(
        self,
        db: AsyncSession,
        group_by_field: str,
        sum_fields: List[str],
        query_params: Optional[BaseQueryParams] = BaseQueryParams()
    ) -> List[dict]:
        """
        Group by one field and sum others.
    
        Example: group_by_field='product_id', sum_fields=['quantity', 'total']
        """
        group_col = getattr(self.model, group_by_field)
        sum_alias_map = {f: f"sum_{f}" for f in sum_fields}
    
        sum_cols = [
            func.sum(getattr(self.model, f)).label(sum_alias_map[f])
            for f in sum_fields
        ]
    
        stmt: Select = (
            select(group_col.label(group_by_field), *sum_cols)
            .group_by(group_col)
        )
    
        # Allow sorting by aggregated fields like "sum_quantity"
        if query_params.order_by:
            if query_params.order_by in sum_alias_map.values():
                order_col = literal_column(query_params.order_by)
            else:
                order_col = getattr(self.model, query_params.order_by, None)
    
            if order_col is not None:
                stmt = stmt.order_by(
                    asc(order_col) if query_params.sort.lower() == "asc" else desc(order_col))
    
        if query_params.limit is not None:
            stmt = stmt.offset(query_params.offset).limit(query_params.limit)
    
        result = await db.execute(stmt)
        rows = result.all()
    
        return [
            {group_by_field: row[0], **{f"sum_{f}": row[i+1]
                                        for i, f in enumerate(sum_fields)}}
            for row in rows
        ]

    @handle_db_exceptions()
    async def create(self, db: AsyncSession, obj_data: dict) -> ModelType:
        """Create a new record."""
        obj = self.model(**obj_data)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    @handle_db_exceptions()
    async def update(self, db: AsyncSession, id: int, obj_data: dict) -> ModelType:
        """Update a record."""
        obj = await self.get_one(db, id=id)
        if obj is None:
            error_text = f"{self.model.__name__} with ID {id} not found"
            raise NoResultFound(error_text)

        for key, value in obj_data.items():
            setattr(obj, key, value)
        await db.flush()
        await db.refresh(obj)
        return obj

    @handle_db_exceptions()
    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Delete a record."""
        obj = await self.get_one(db, id=id)
        if obj:
            await db.delete(obj)
            await db.flush()
            return True

        return False
