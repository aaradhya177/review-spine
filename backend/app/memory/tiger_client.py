from dataclasses import dataclass
from math import sqrt

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

    async def vector_search(
        self,
        *,
        repo: str,
        query_embedding: list[float],
        top_k: int,
    ) -> list[tuple[CodeChunkRecord, float]]:
        chunks = await self.list_chunks(repo=repo)
        scored = [
            (chunk, cosine_similarity(query_embedding, chunk.embedding))
            for chunk in chunks
        ]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]

    async def keyword_search(
        self,
        *,
        repo: str,
        query: str,
        top_k: int,
    ) -> list[tuple[CodeChunkRecord, float]]:
        terms = tokenize(query)
        chunks = await self.list_chunks(repo=repo)
        scored = []
        for chunk in chunks:
            content_terms = tokenize(chunk.content + " " + chunk.path)
            score = sum(content_terms.count(term) for term in terms)
            if score > 0:
                scored.append((chunk, float(score)))
        return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]


def tokenize(text: str) -> list[str]:
    return [
        part.lower()
        for part in "".join(char if char.isalnum() else " " for char in text).split()
    ]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    left = left[:length]
    right = right[:length]
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)

