from collections.abc import Callable

from fastapi import Header, HTTPException, status


def require_role(role: str) -> Callable:
    async def dependency(x_review_spine_role: str | None = Header(default=None)) -> str:
        roles = {item.strip() for item in (x_review_spine_role or "").split(",") if item.strip()}
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {role}",
            )
        return role

    return dependency

