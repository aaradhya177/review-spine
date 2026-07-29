import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import RepoFileIndexRecord, now_utc
from app.memory.embedder import Embedder
from app.memory.tiger_client import CodeChunkInput, TigerMemoryClient

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


@dataclass(frozen=True)
class IngestionResult:
    files_seen: int
    files_indexed: int
    chunks_written: int


class CodeIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        embedder: Embedder,
        chunk_size: int = 1200,
    ):
        self.session = session
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.memory = TigerMemoryClient(session)

    async def ingest_repo(self, *, repo: str, root: Path) -> IngestionResult:
        files_seen = 0
        files_indexed = 0
        chunks_written = 0
        for path in sorted(self._iter_source_files(root)):
            files_seen += 1
            relative_path = path.relative_to(root).as_posix()
            content = path.read_text(encoding="utf-8")
            content_hash = self._hash(content)
            if not await self._should_index(
                repo=repo,
                path=relative_path,
                content_hash=content_hash,
            ):
                continue

            chunks = await self._build_chunks(
                repo=repo,
                path=relative_path,
                content=content,
                content_hash=content_hash,
            )
            await self.memory.replace_file_chunks(
                repo=repo,
                path=relative_path,
                chunks=chunks,
            )
            await self._upsert_file_index(
                repo=repo,
                path=relative_path,
                content_hash=content_hash,
            )
            files_indexed += 1
            chunks_written += len(chunks)
        return IngestionResult(
            files_seen=files_seen,
            files_indexed=files_indexed,
            chunks_written=chunks_written,
        )

    async def _build_chunks(
        self,
        *,
        repo: str,
        path: str,
        content: str,
        content_hash: str,
    ) -> list[CodeChunkInput]:
        parts = chunk_text(content, chunk_size=self.chunk_size)
        chunks = []
        for index, part in enumerate(parts):
            chunks.append(
                CodeChunkInput(
                    repo=repo,
                    path=path,
                    symbol=None,
                    chunk_index=index,
                    content=part,
                    embedding=await self.embedder.embed(part),
                    token_count=count_tokens_roughly(part),
                    content_hash=content_hash,
                )
            )
        return chunks

    async def _should_index(self, *, repo: str, path: str, content_hash: str) -> bool:
        result = await self.session.execute(
            select(RepoFileIndexRecord).where(
                RepoFileIndexRecord.repo == repo,
                RepoFileIndexRecord.path == path,
            )
        )
        record = result.scalar_one_or_none()
        return record is None or record.content_hash != content_hash

    async def _upsert_file_index(self, *, repo: str, path: str, content_hash: str) -> None:
        result = await self.session.execute(
            select(RepoFileIndexRecord).where(
                RepoFileIndexRecord.repo == repo,
                RepoFileIndexRecord.path == path,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            self.session.add(
                RepoFileIndexRecord(repo=repo, path=path, content_hash=content_hash)
            )
        else:
            record.content_hash = content_hash
            record.last_indexed_at = now_utc()
        await self.session.flush()

    def _iter_source_files(self, root: Path):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in DEFAULT_IGNORED_DIRS for part in path.parts):
                continue
            if is_probably_binary(path):
                continue
            yield path

    def _hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


def chunk_text(text: str, *, chunk_size: int) -> list[str]:
    if not text:
        return []
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    current = ""
    for line in lines:
        if current and len(current) + len(line) > chunk_size:
            chunks.append(current)
            current = ""
        current += line
    if current:
        chunks.append(current)
    return chunks


def count_tokens_roughly(text: str) -> int:
    return max(1, len(text.split()))


def is_probably_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:1024]
    except OSError:
        return True
    return b"\x00" in chunk

