from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Query, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import clerk_auth, UserPrincipal

reusable_oauth2 = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> UserPrincipal:
    return await clerk_auth.verify_token(token.credentials)

async def get_ws_user(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> UserPrincipal:
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        return await clerk_auth.verify_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise
