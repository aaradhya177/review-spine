import hashlib
from typing import Protocol


class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for text."""


class FakeEmbedder:
    def __init__(self, *, dimensions: int = 8):
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for index in range(self.dimensions):
            byte = digest[index % len(digest)]
            values.append(round((byte / 255.0) * 2 - 1, 6))
        return values

