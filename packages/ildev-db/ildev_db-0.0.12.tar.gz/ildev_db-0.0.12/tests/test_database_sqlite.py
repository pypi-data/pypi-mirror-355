import pytest
import logging
from db.base_database import BaseDatabase
from log.base_log import BaseLog

DATABASE_URL = "sqlite+aiosqlite:///./test_database.db"

@pytest.mark.asyncio
async def test_db_connection():
    """Test database session creation."""
    log_folder = "../logs"
    log_file = "tests.log"
    logger = BaseLog(str(log_folder), log_file, logging.DEBUG)
    db = BaseDatabase(DATABASE_URL, logger)
    get_db = db.get_db_session()

    async for db in get_db():
        assert db is not None
