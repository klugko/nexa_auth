from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.presentation.api.v1.rbac_routes import router as rbac_router
from app.presentation.deps.current_user import get_current_user

class FakeRole:
    def __init__(self, name): self.name = name

class FakeUser:
    def __init__(self, roles): self.roles = [FakeRole(r) for r in roles]

def test_admin_guard_allows():
    app = FastAPI()
    app.include_router(rbac_router)

    async def fake_admin():
        return FakeUser(["admin"])
    app.dependency_overrides[get_current_user] = fake_admin

    client = TestClient(app)
    r = client.get("/api/v1/rbac/admin-ping")
    assert r.status_code == 200
    assert r.json()["scope"] == "admin"

def test_user_forbidden_on_admin():
    app = FastAPI()
    app.include_router(rbac_router)

    async def fake_user():
        return FakeUser(["user"])
    app.dependency_overrides[get_current_user] = fake_user

    client = TestClient(app)
    r = client.get("/api/v1/rbac/admin-ping")
    assert r.status_code == 403

def test_manager_or_admin_allows_manager():
    app = FastAPI()
    app.include_router(rbac_router)

    async def fake_manager():
        return FakeUser(["manager"])
    app.dependency_overrides[get_current_user] = fake_manager

    client = TestClient(app)
    r = client.get("/api/v1/rbac/manager-or-admin")
    assert r.status_code == 200
    assert r.json()["scope"] == "manager|admin"
