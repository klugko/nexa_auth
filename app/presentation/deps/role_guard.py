from typing import Iterable, Set
from fastapi import Depends, HTTPException, status
from app.presentation.deps.current_user import get_current_user
from app.domain.entities.user import User

def require_roles(*required: str):
    """
    Guard réutilisable.
    - Autorise si l'utilisateur possède AU MOINS un rôle parmi 'required'
    - 'admin' sur l'utilisateur passe partout
    - Si aucun rôle requis n'est passé -> autorisé
    """
    req_set: Set[str] = set(r.strip().lower() for r in required if r and r.strip())

    async def _guard(user: User = Depends(get_current_user)):
        if not req_set:
            return user
        user_roles = {r.name.lower() for r in (user.roles or [])}
        if "admin" in user_roles:
            return user
        if user_roles.intersection(req_set):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    return _guard
