from typing import Protocol, Tuple

class StorageService(Protocol):
    async def save_avatar(self, *, user_id: str, content: bytes, ext: str) -> str:
        """
        Enregistre le fichier et retourne l'URL publique (ou chemin relatif servi par l'API).
        `ext` sans point (e.g., 'png', 'jpg', 'webp').
        """
        ...
