from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.presentation.deps.current_user import get_current_user
from app.domain.entities.user import User
from app.application.use_cases.resume_use_cases import ResumeUseCases
from app.presentation.schemas.resume_schema import SkillsResponse

router = APIRouter(prefix="/api/v1/users/me", tags=["Users • Resume/Skills"])
uc = ResumeUseCases()

@router.post("/cv", response_model=SkillsResponse, summary="Upload my resume (PDF/DOCX) and extract skills")
async def upload_cv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    raw = await file.read()
    skills = await uc.upload_and_parse(db,
                                       user=current_user,
                                       filename=file.filename or "resume",
                                       content_type=file.content_type or "",
                                       raw=raw)
    return {"items": skills}

@router.get("/skills", response_model=SkillsResponse, summary="List my extracted skills")
async def get_skills(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = await uc.list_my_skills(db, user=current_user)
    return {"items": items}
