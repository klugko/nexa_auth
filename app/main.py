from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.config import settings
from app.presentation.api.v1 import auth_routes

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    swagger_ui_parameters={"persistAuthorization": True}
)

# Routes
app.include_router(auth_routes.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi