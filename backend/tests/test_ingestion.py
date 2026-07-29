from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.ingestion import CodeIngestionService, chunk_text
from app.database import Base, create_async_sessionmaker, create_engine
from app.memory import FakeEmbedder, TigerMemoryClient


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


def test_chunk_text_preserves_line_groups() -> None:
    chunks = chunk_text("a\nbb\nccc\n", chunk_size=5)

    assert chunks == ["a\nbb\n", "ccc\n"]


@pytest.mark.asyncio
async def test_ingestion_indexes_changed_files_only(
    session: AsyncSession,
    tmp_path: Path,
) -> None:
    source = tmp_path / "repo"
    source.mkdir()
    (source / "app.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")

    service = CodeIngestionService(
        session,
        embedder=FakeEmbedder(dimensions=4),
        chunk_size=100,
    )

    first = await service.ingest_repo(repo="acme/shop", root=source)
    second = await service.ingest_repo(repo="acme/shop", root=source)
    await session.commit()

    chunks = await TigerMemoryClient(session).list_chunks(repo="acme/shop", path="app.py")
    assert first.files_indexed == 1
    assert first.chunks_written == 1
    assert second.files_indexed == 0
    assert len(chunks) == 1
    assert len(chunks[0].embedding) == 4


@pytest.mark.asyncio
async def test_ingestion_replaces_chunks_when_file_changes(
    session: AsyncSession,
    tmp_path: Path,
) -> None:
    source = tmp_path / "repo"
    source.mkdir()
    file_path = source / "app.py"
    file_path.write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service = CodeIngestionService(
        session,
        embedder=FakeEmbedder(dimensions=4),
        chunk_size=10,
    )

    await service.ingest_repo(repo="acme/shop", root=source)
    file_path.write_text("def hello():\n    return 'hello there'\n", encoding="utf-8")
    second = await service.ingest_repo(repo="acme/shop", root=source)
    await session.commit()

    chunks = await TigerMemoryClient(session).list_chunks(repo="acme/shop", path="app.py")
    assert second.files_indexed == 1
    assert second.chunks_written == len(chunks)
    assert any("hello there" in chunk.content for chunk in chunks)

