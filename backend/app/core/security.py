import os
import time
import httpx
from typing import Any, Dict, Optional
from jose import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

class UserPrincipal(BaseModel):
    user_id: str
    email: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ClerkAuthenticator:
    def __init__(self):
        self.clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
        self.jwks_url = "https://api.clerk.com/v1/jwks"
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._last_fetch = 0
        self._cache_ttl = 3600

    async def _get_jwks(self) -> Dict[str, Any]:
        now = time.time()
        if self._jwks_cache and (now - self._last_fetch < self._cache_ttl):
            return self._jwks_cache
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.clerk_secret_key}"}
            response = await client.get(self.jwks_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not fetch auth configuration from Clerk"
                )
            self._jwks_cache = response.json()
            self._last_fetch = now
            return self._jwks_cache

    async def verify_token(self, token: str) -> UserPrincipal:
        try:
            unverified_header = jwt.get_unverified_header(token)
            jwks = await self._get_jwks()
            rsa_key = {}
            for key in jwks.get("keys", []):
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if not rsa_key:
                raise HTTPException(status_code=401, detail="Invalid token header")
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                options={"verify_at_hash": False}
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing subject")
            return UserPrincipal(
                user_id=user_id,
                email=payload.get("email"),
                metadata=payload.get("metadata", {})
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

clerk_auth = ClerkAuthenticator()
