import os
import time
from typing import Optional
from app.config import settings

class LocalStorageService:
    """
    Stocke les avatars sur le disque local.
    Sert les fichiers via StaticFiles monté sur settings.storage_public_base_path.
    """

    def __init__(self):
        os.makedirs(settings.storage_local_dir, exist_ok=True)

    async def save_avatar(self, *, user_id: str, content: bytes, ext: str) -> str:
        ts = int(time.time())
        filename = f"{user_id}_{ts}.{ext.lower()}"
        abs_path = os.path.join(settings.storage_local_dir, filename)
        # écriture atomique
        tmp_path = abs_path + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(content)
        os.replace(tmp_path, abs_path)
        # URL publique (servie par StaticFiles)
        base = settings.storage_public_base_path.rstrip("/")
        return f"{base}/{filename}"
