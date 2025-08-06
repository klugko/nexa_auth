from fastapi import FastAPI
from app.config import settings
from app.presentation.api.v1 import auth_routes

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    swagger_ui_parameters={"persistAuthorization": True},
    openapi_url="/openapi.json"
)

# Personnalisation du bouton Authorize
app.openapi_schema = app.openapi()
app.openapi_schema["components"]["securitySchemes"] = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
}
app.openapi_schema["security"] = [{"BearerAuth": []}]

app.include_router(auth_routes.router)
