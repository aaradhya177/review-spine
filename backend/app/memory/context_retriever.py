from dataclasses import dataclass

from app.memory.embedder import Embedder
from app.memory.tiger_client import TigerMemoryClient


@dataclass(frozen=True)
class RetrievedContext:
    path: str
    symbol: str | None
    content: str
    rank: int
    score: float
    method: str


class ContextRetriever:
    def __init__(
        self,
        memory_client: TigerMemoryClient,
        *,
        embedder: Embedder,
        rrf_k: int = 60,
    ):
        self.memory_client = memory_client
        self.embedder = embedder
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        *,
        repo: str,
        diff_text: str,
        changed_files: list[str],
        agent_type: str,
        top_k: int = 5,
    ) -> list[RetrievedContext]:
        query = "\n".join([agent_type, *changed_files, diff_text])
        embedding = await self.embedder.embed(query)
        vector_results = await self.memory_client.vector_search(
            repo=repo,
            query_embedding=embedding,
            top_k=top_k,
        )
        keyword_results = await self.memory_client.keyword_search(
            repo=repo,
            query=query,
            top_k=top_k,
        )
        fused = reciprocal_rank_fusion(
            vector_results=vector_results,
            keyword_results=keyword_results,
            rrf_k=self.rrf_k,
        )
        return [
            RetrievedContext(
                path=chunk.path,
                symbol=chunk.symbol,
                content=chunk.content,
                rank=index + 1,
                score=score,
                method=method,
            )
            for index, (chunk, score, method) in enumerate(fused[:top_k])
        ]


def reciprocal_rank_fusion(
    *,
    vector_results,
    keyword_results,
    rrf_k: int,
):
    scores = {}
    chunks = {}
    methods = {}
    for method, results in (("vector", vector_results), ("keyword", keyword_results)):
        for rank, (chunk, _score) in enumerate(results, start=1):
            key = chunk.id
            chunks[key] = chunk
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            methods.setdefault(key, set()).add(method)
    return [
        (chunks[key], score, "+".join(sorted(methods[key])))
        for key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]

