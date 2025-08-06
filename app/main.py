from fastapi import FastAPI
from app.config import settings
from app.presentation.api.v1 import auth_routes

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.include_router(auth_routes.router)

@app.get("/")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
