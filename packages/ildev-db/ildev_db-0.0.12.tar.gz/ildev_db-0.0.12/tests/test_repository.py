import pytest
from db.base_repository import BaseRepository
from db.base_model import Base
from db.base_query_params import BaseQueryParams
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.exc import NoResultFound
from db.exception import BaseRepositoryError

class AggregatableModel(Base):
    __tablename__ = "aggregatable_models"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Float)
    unit_price = Column(Float)
    total = Column(Float)
    product_id = Column(Integer, index=True)
    basket_id = Column(Integer)

class TestModel(Base):
    __tablename__ = "test_models"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

@pytest.fixture()
def test_repository():
    """Fixture for creating a repository instance."""
    return BaseRepository(TestModel)

@pytest.fixture()
def aggregatable_repository():
    return BaseRepository(AggregatableModel)

@pytest.mark.asyncio
async def test_get_one(test_db: AsyncSession, test_repository: BaseRepository):
    """Test creating and retrieving an object."""
    async with test_db.begin():
        obj_data = {"id": 1, "name": "Test Object"}
        obj = await test_repository.create(test_db, obj_data)
        assert obj.id == obj_data.get("id")
        assert obj.name == obj_data.get("name")

        retrieved_obj = await test_repository.get_one(test_db, id=obj_data.get("id"))
        assert retrieved_obj is not None
        assert retrieved_obj.id == obj.id
        assert retrieved_obj.name == obj.name

@pytest.mark.asyncio
async def test_get_all(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'get_all' method"""
    async with test_db.begin():
        items_count = 10
        for i in range(items_count):
            obj_data = {"id": i, "name": f"Test Object {i}"}
            await test_repository.create(test_db, obj_data)

        result = await test_repository.get_all(test_db)
        assert len(result) == items_count
        for i, obj in enumerate(result):
            assert obj.name == f"Test Object {i}"

@pytest.mark.asyncio
async def test_get_all_limited(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'get_all' method"""
    async with test_db.begin():
        for i in range(10):
            obj_data = {"id": i, "name": f"Test Object {i}"}
            await test_repository.create(test_db, obj_data)

        limit = 5
        query_params = BaseQueryParams(limit=limit)
        result = await test_repository.get_all(test_db, query_params=query_params)
        assert len(result) == limit
        for i, obj in enumerate(result):
            assert obj.name == f"Test Object {i}"

@pytest.mark.asyncio
async def test_get_all_filtered(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'get_all' method"""
    async with test_db.begin():
        for i in range(10):
            obj_data = {"id": i, "name": f"Test Object {i}"}
            await test_repository.create(test_db, obj_data)

        filter_data = {"name": "Test Object 1"}
        query_params = BaseQueryParams(filters=filter_data)
        result = await test_repository.get_all(test_db, query_params=query_params)
        assert len(result) == 1 
        assert result[0].name ==  filter_data.get("name")

@pytest.mark.asyncio
async def test_get_not_found(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'get' when object is not found"""   
    async with test_db.begin():
        get_data = {"name": "Not found Object"}
        retrieved_obj = await test_repository.get_one(test_db, name=get_data.get("name")) # No exception should be raised
        assert retrieved_obj is None

@pytest.mark.asyncio
async def test_group_by_sum(test_db: AsyncSession, aggregatable_repository: BaseRepository):
    """Test group_by_sum method with product_id and sum of quantity."""
    async with test_db.begin():
        data = [
            {"id": 1, "quantity": 2.0, "unit_price": 670.0, "total": 1340.0, "product_id": 1, "basket_id": 1},
            {"id": 2, "quantity": 1.0, "unit_price": 59.99, "total": 59.99, "product_id": 2, "basket_id": 2},
            {"id": 3, "quantity": 1.0, "unit_price": 59.99, "total": 59.99, "product_id": 2, "basket_id": 2},
            {"id": 34, "quantity": 1.0, "unit_price": 74.99, "total": 74.99, "product_id": 2, "basket_id": 8},
            {"id": 4, "quantity": 1.0, "unit_price": 249.99, "total": 249.99, "product_id": 3, "basket_id": 2},
            {"id": 38, "quantity": 1.0, "unit_price": 249.99, "total": 249.99, "product_id": 3, "basket_id": 8},
            {"id": 50, "quantity": 1.0, "unit_price": 249.99, "total": 249.99, "product_id": 3, "basket_id": 14},
            {"id": 67, "quantity": 1.0, "unit_price": 269.99, "total": 269.99, "product_id": 3, "basket_id": 17},
            {"id": 5, "quantity": 1.0, "unit_price": 84.7, "total": 84.7, "product_id": 4, "basket_id": 3},
            {"id": 6, "quantity": 1.0, "unit_price": 149.0, "total": 149.0, "product_id": 5, "basket_id": 3},
        ]

        for item in data:
            await aggregatable_repository.create(test_db, item)

        query_params = BaseQueryParams(order_by="sum_quantity", sort="desc", limit=10)
        result = await aggregatable_repository.group_by_sum(
            db=test_db,
            group_by_field="product_id",
            sum_fields=["quantity"],
            query_params=query_params
        )

        assert isinstance(result, list)
        assert len(result) == 5  # 5 unique product_ids

        expected = {
            1: 2.0,
            2: 3.0,
            3: 4.0,
            4: 1.0,
            5: 1.0,
        }

        for row in result:
            pid = row["product_id"]
            assert round(row["sum_quantity"], 2) == expected[pid]



@pytest.mark.asyncio
async def test_create(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'create' method"""
    async with test_db.begin():
        obj_data = {"id": 1, "name": "Test Object"}
        obj = await test_repository.create(test_db, obj_data)
        assert obj.id == obj_data.get("id")
        assert obj.name == obj_data.get("name")

        retrieved_obj = await test_repository.get_one(test_db, id=obj_data.get("id"))
        assert retrieved_obj is not None
        assert retrieved_obj.id == obj.id
        assert retrieved_obj.name == obj.name

@pytest.mark.asyncio
async def test_update(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'update' method"""
    async with test_db.begin():
        obj_data = {"id": 1, "name": "Test Object"}
        obj = await test_repository.create(test_db, obj_data)

        update_data = {"name": "Updated Object"}
        updated_obj = await test_repository.update(test_db, obj.id, update_data)
        assert updated_obj is not None
        assert updated_obj.name == update_data.get("name")

        db_obj = await test_repository.get_one(test_db, id=obj_data.get("id"))
        assert db_obj.name == update_data.get("name")

@pytest.mark.asyncio
async def test_update_not_found(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'update' when object is not found"""
    with pytest.raises(BaseRepositoryError):
        async with test_db.begin():
            update_data = {"name": "Updated Object"}
            await test_repository.update(test_db, 999, update_data)

@pytest.mark.asyncio
async def test_delete(test_db: AsyncSession, test_repository: BaseRepository):
    """Test deleting an object."""
    async with test_db.begin():
        obj_data = {"id": 1, "name": "Test Object"}
        obj = await test_repository.create(test_db, obj_data)

        await test_repository.delete(test_db, obj.id)

        deleted_obj = await test_repository.get_one(test_db, id=obj_data.get("id"))
        assert deleted_obj is None

@pytest.mark.asyncio
async def test_delete_not_found(test_db: AsyncSession, test_repository: BaseRepository):
    """Test 'delete' when object is not found"""
    async with test_db.begin():
        await test_repository.delete(test_db, 999)  # No exception should be raised
