import os
import time
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.repositories.user_resume_repository_impl import UserResumeRepositoryImpl
from app.infrastructure.repositories.user_skill_repository_impl import UserSkillRepositoryImpl
from app.infrastructure.services.resume_text_extractor import ResumeTextExtractor
from app.infrastructure.services.resume_parser_service import ResumeParserService

resume_repo = UserResumeRepositoryImpl()
skill_repo  = UserSkillRepositoryImpl()
parser      = ResumeParserService()

ALLOWED_MIME = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXT  = {".pdf", ".docx"}
MAX_BYTES    = 10 * 1024 * 1024  # 10MB

class ResumeUseCases:
    async def upload_and_parse(self, db: AsyncSession, *, user, filename: str, content_type: str, raw: bytes):
        if content_type not in ALLOWED_MIME or os.path.splitext(filename)[1].lower() not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail="Fichier non supporté (PDF/DOCX)")
        if len(raw) > MAX_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Fichier trop volumineux")

        os.makedirs(settings.resumes_local_dir, exist_ok=True)
        ts = int(time.time())
        safe_name = f"{user.id}_{ts}{os.path.splitext(filename)[1].lower()}"
        abs_path = os.path.join(settings.resumes_local_dir, safe_name)
        tmp_path = abs_path + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(raw)
        os.replace(tmp_path, abs_path)

        resume = await resume_repo.create_or_replace(db, user.id, abs_path)

        text = ResumeTextExtractor.extract_text(safe_name, raw).strip()
        if not text:
            raise HTTPException(status_code=400, detail="Impossible d'extraire du texte du CV")

        skills = await parser.extract_skills(text)  
        await skill_repo.upsert_bulk(db, user.id, skills)
        await resume_repo.set_parsed_now(db, resume)

        return [{"skill": s, "score": sc} for (s, sc) in skills]

    async def list_my_skills(self, db: AsyncSession, *, user):
        items = await skill_repo.list_for_user(db, user.id)
        return [{"skill": it.skill, "score": it.score} for it in items]
