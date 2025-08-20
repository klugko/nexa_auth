from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.services.audit_logger import audit_logger

jwt = JWTService()

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        try:
            user_id = None
            auth = request.headers.get("authorization") or request.headers.get("Authorization")
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
                payload = jwt.decode_token(token)
                sub = payload.get("sub")
                if sub:
                    user_id = sub

            await audit_logger.log(
                user_id=user_id,
                action="http.request",
                resource=request.url.path,
                ip=(request.client.host if request.client else None),
                ua=request.headers.get("user-agent"),
                meta={
                    "method": request.method,
                    "status": response.status_code,
                },
            )
        except Exception:
            pass

        return response
