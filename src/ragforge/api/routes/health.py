import asyncio

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ragforge.infrastructure.chroma import get_chroma_client
from ragforge.infrastructure.database import SessionFactory

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    try:
        async with asyncio.timeout(5):
            async with SessionFactory() as session:
                await session.execute(text("SELECT 1"))

            client = get_chroma_client()
            await asyncio.to_thread(client.heartbeat)

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="A required dependency is unavailable",
        ) from exc

    return {"status": "ready"}
