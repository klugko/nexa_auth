from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create async engine
engine = create_async_engine(settings.database_url, echo=True, future=True)

# Create async session
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency injection for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
