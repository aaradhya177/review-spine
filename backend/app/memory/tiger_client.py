from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CodeChunkRecord


@dataclass(frozen=True)
class CodeChunkInput:
    repo: str
    path: str
    symbol: str | None
    chunk_index: int
    content: str
    embedding: list[float]
    token_count: int
    content_hash: str


class TigerMemoryClient:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def replace_file_chunks(
        self,
        *,
        repo: str,
        path: str,
        chunks: list[CodeChunkInput],
    ) -> list[CodeChunkRecord]:
        await self.session.execute(
            delete(CodeChunkRecord).where(
                CodeChunkRecord.repo == repo,
                CodeChunkRecord.path == path,
            )
        )
        records = [
            CodeChunkRecord(
                repo=chunk.repo,
                path=chunk.path,
                symbol=chunk.symbol,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=chunk.embedding,
                token_count=chunk.token_count,
                content_hash=chunk.content_hash,
            )
            for chunk in chunks
        ]
        self.session.add_all(records)
        await self.session.flush()
        return records

    async def list_chunks(self, *, repo: str, path: str | None = None) -> list[CodeChunkRecord]:
        query = select(CodeChunkRecord).where(CodeChunkRecord.repo == repo)
        if path is not None:
            query = query.where(CodeChunkRecord.path == path)
        result = await self.session.execute(
            query.order_by(CodeChunkRecord.path, CodeChunkRecord.chunk_index)
        )
        return list(result.scalars())

