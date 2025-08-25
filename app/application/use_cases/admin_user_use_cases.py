from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.security.password_hash import hash_password

user_repo = UserRepositoryImpl()

class AdminUserUseCases:
    async def list_users(
        self,
        db: AsyncSession,
        *,
        keyword: Optional[str],
        page: int,
        size: int,
        sort_by: str,
        sort_dir: str,
    ):
        return await user_repo.list_paginated(
            db,
            keyword=keyword,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    async def create_user(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        phone: Optional[str],
        position: Optional[str],
        is_active: bool,
        email_verified: Optional[bool],
    ):
        existing = await user_repo.get_by_email(db, email)
        if existing:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        from app.domain.entities.user import User
        hashed = hash_password(password) if password else None
        user = User(
            email=email,
            hashed_password=hashed,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            position=position,
            is_active=is_active,
            email_verified=email_verified if email_verified is not None else False,
        )
        created = await user_repo.create(db, user)
        return created
    
    async def update_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        email: Optional[str],
        new_password: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        phone: Optional[str],
        position: Optional[str],
        is_active: Optional[bool],
        email_verified: Optional[bool],
    ):
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

        update_fields = {}
        if email and email != user.email:
            other = await user_repo.get_by_email(db, email)
            if other and other.id != user.id:
                raise HTTPException(status_code=400, detail="Email déjà utilisé")
            update_fields["email"] = email

        if new_password:
            update_fields["hashed_password"] = hash_password(new_password)
        if first_name is not None: update_fields["first_name"] = first_name
        if last_name is not None: update_fields["last_name"] = last_name
        if phone is not None: update_fields["phone"] = phone
        if position is not None: update_fields["position"] = position
        if is_active is not None: update_fields["is_active"] = is_active
        if email_verified is not None: update_fields["email_verified"] = email_verified

        if not update_fields:
            return user

        updated = await user_repo.update_admin(db, user, **update_fields)
        return updated

    async def delete_user(self, db: AsyncSession, *, user_id: UUID) -> None:
        ok = await user_repo.delete_by_id(db, user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
