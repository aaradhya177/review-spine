class InMemoryIdempotencyGuard:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    async def reserve(self, key: str) -> bool:
        if key in self.keys:
            return False
        self.keys.add(key)
        return True

