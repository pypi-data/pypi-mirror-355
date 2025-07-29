from log.base_log import BaseLog

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

class BaseDatabase:
    def __init__(self, database_url: str, logger: BaseLog):
        self.logger = logger
        self.database_url = database_url
        self.engine = self.get_engine()
        self.session_factory = self.get_session_factory()

    def get_engine(self):
        """Creates and returns a single database engine."""
        self.logger.info(f"Creating database engine for {self.database_url}")
        return create_async_engine(self.database_url, echo=False)

    def get_session_factory(self):
        """Creates and returns a session factory using the provided engine."""
        self.logger.info("Creating session factory")
        return sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provides an async database session generator."""
        async def get_db() -> AsyncGenerator[AsyncSession, None]:
            async with self.session_factory() as session:
                self.logger.debug("Creating new database session")
                try:
                    yield session
                except Exception as e:
                    self.logger.error(f"Error in database session: {e}")
                    raise
                finally:
                    self.logger.debug("Closing database session")

        return get_db
