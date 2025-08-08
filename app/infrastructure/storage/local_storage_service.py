import os
import time
from typing import Final

import aiofiles

from app.config import settings
from app.infrastructure.storage.storage_service import StorageService

class LocalStorageService(StorageService):
    """
    Implémentation locale de StorageService.
    - Stocke les fichiers d'avatar dans `settings.storage_local_dir`
    - Retourne une URL publique relative sous `settings.storage_public_base_path`
    - Écriture atomique + nommage déterministe (user_id + timestamp)
    """

    _dir: Final[str]
    _base_path: Final[str]

    def __init__(self) -> None:
        self._dir = settings.storage_local_dir
        self._base_path = settings.storage_public_base_path.rstrip("/")
        os.makedirs(self._dir, exist_ok=True)

    async def save_avatar(self, *, user_id: str, content: bytes, ext: str) -> str:
        """
        Sauvegarde le fichier et retourne un chemin public (ex: /static/avatars/xxxx.png).
        """
        ext = ext.lower().strip(".")
        ts = int(time.time())
        filename = f"{user_id}_{ts}.{ext}"
        abs_path = os.path.join(self._dir, filename)

        tmp_path = abs_path + ".tmp"
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(content)
        os.replace(tmp_path, abs_path)

        return f"{self._base_path}/{filename}"
