from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer
from app.config import settings

clerk_config = ClerkConfig(jwks_url=settings.CLERK_JWKS_URL)
clerk_auth_guard = ClerkHTTPBearer(config=clerk_config, add_state=True)
