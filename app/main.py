from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import os
from starlette.staticfiles import StaticFiles
from app.config import settings
from app.presentation.api.v1 import auth_routes, user_resume_routes, user_skill_summary_routes, well_known_routes
from app.presentation.exception_handlers import register_exception_handlers
from app.presentation.api.v1 import user_routes
from app.presentation.api.v1 import rbac_routes
from app.presentation.api.v1 import admin_user_roles_routes
from app.presentation.api.v1 import admin_users_crud_routes
from app.presentation.api.v1 import invitations_routes


app = FastAPI(title=settings.app_name, version=settings.app_version)

os.makedirs(settings.storage_local_dir, exist_ok=True)
app.mount(settings.storage_public_base_path, StaticFiles(directory=settings.storage_local_dir), name="avatars")

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_routes.router)         
app.include_router(well_known_routes.router)  
app.include_router(user_routes.router) 
app.include_router(rbac_routes.router)
app.include_router(admin_user_roles_routes.router)
app.include_router(admin_users_crud_routes.router)
app.include_router(invitations_routes.router)
app.include_router(user_resume_routes.router)
app.include_router(user_skill_summary_routes.router)

# Exceptions
register_exception_handlers(app)

# Swagger/OpenAPI: BearerAuth + tags
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="Nexa Auth API — JWT RS256, OAuth2 Providers, User Management",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
