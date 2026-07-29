from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, create_async_sessionmaker, create_engine
from app.memory import CodeChunkInput, ContextRetriever, FakeEmbedder, TigerMemoryClient


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


async def seed_chunks(session: AsyncSession) -> TigerMemoryClient:
    memory = TigerMemoryClient(session)
    embedder = FakeEmbedder(dimensions=4)
    chunks = []
    for index, (path, content) in enumerate(
        [
            ("billing/stripe.py", "def charge_customer(customer_id): pass"),
            ("auth/session.py", "def refresh_session(token): pass"),
            ("tests/test_billing.py", "def test_duplicate_charge(): pass"),
        ]
    ):
        chunks.append(
            CodeChunkInput(
                repo="acme/shop",
                path=path,
                symbol=None,
                chunk_index=0,
                content=content,
                embedding=await embedder.embed(content),
                token_count=4,
                content_hash=f"hash-{index}",
            )
        )
    for chunk in chunks:
        await memory.replace_file_chunks(
            repo=chunk.repo,
            path=chunk.path,
            chunks=[chunk],
        )
    await session.commit()
    return memory


@pytest.mark.asyncio
async def test_keyword_search_finds_exact_identifier(session: AsyncSession) -> None:
    memory = await seed_chunks(session)

    results = await memory.keyword_search(
        repo="acme/shop",
        query="duplicate charge_customer",
        top_k=3,
    )

    assert {chunk.path for chunk, _score in results} >= {
        "billing/stripe.py",
        "tests/test_billing.py",
    }


@pytest.mark.asyncio
async def test_context_retriever_returns_deterministic_fused_results(
    session: AsyncSession,
) -> None:
    memory = await seed_chunks(session)
    retriever = ContextRetriever(memory, embedder=FakeEmbedder(dimensions=4))

    results = await retriever.retrieve(
        repo="acme/shop",
        diff_text="charge_customer should prevent duplicate charge",
        changed_files=["billing/stripe.py"],
        agent_type="tests",
        top_k=2,
    )

    assert len(results) == 2
    assert results[0].rank == 1
    assert any(result.path == "billing/stripe.py" for result in results)
    assert all(result.method for result in results)

