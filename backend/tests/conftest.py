import asyncio
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tracelens.config.settings import get_settings
from tracelens.db.session import dispose_engine, get_engine


def postgres_integration_enabled() -> bool:
    return os.environ.get("TRACELENS_INTEGRATION_TESTS", "").lower() in {
        "1",
        "true",
        "yes",
    }


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: tests requiring Postgres (set TRACELENS_INTEGRATION_TESTS=1)",
    )


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    return Config("alembic.ini")


async def _postgres_is_reachable() -> bool:
    get_settings.cache_clear()
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except OSError:
        return False
    except Exception:
        return False
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def migrated_schema(alembic_config: Config) -> None:
    if not postgres_integration_enabled():
        pytest.skip("Postgres integration tests disabled (TRACELENS_INTEGRATION_TESTS=1)")

    if not asyncio.run(_postgres_is_reachable()):
        pytest.skip("Postgres not reachable; run docker compose up postgres")

    get_settings.cache_clear()
    command.upgrade(alembic_config, "head")


@pytest_asyncio.fixture
async def db_session(migrated_schema: None) -> AsyncIterator[AsyncSession]:
    await dispose_engine()
    get_settings.cache_clear()

    factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
