import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from app.config import settings
from app.infrastructure.db.session import async_session_maker 
from app.infrastructure.repositories.audit_log_repository_impl import AuditLogRepositoryImpl

_mask_re_email = re.compile(r"(^|\b)([A-Z0-9._%+-]+)@([A-Z0-9.-]+)\.([A-Z]{2,})($|\b)", re.I)
_mask_re_phone = re.compile(r"\+?\d[\d\s\-()]{6,}", re.I)

def _mask_value(v: str) -> str:
    # masque email/phone basique
    if not isinstance(v, str):
        return v
    v = _mask_re_email.sub(lambda m: f"{m.group(1)}***@{m.group(3)}.{m.group(4)}{m.group(5)}", v)
    v = _mask_re_phone.sub("***", v)
    return v

def _mask_meta(meta: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not meta:
        return None
    out = {}
    for k, v in meta.items():
        lk = k.lower()
        if lk in {"password","token","refresh_token","access_token","authorization","secret"}:
            out[k] = "***"
        elif isinstance(v, str):
            out[k] = _mask_value(v)
        elif isinstance(v, dict):
            out[k] = _mask_meta(v)
        elif isinstance(v, list):
            out[k] = [_mask_value(x) if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    return out

class AuditLogger:
    def __init__(self) -> None:
        self.enabled = str(settings.audit_enabled).lower() == "true"
        self.batch_size = int(getattr(settings, "audit_batch_size", 100))
        self.flush_interval = int(getattr(settings, "audit_flush_interval_seconds", 2))
        self.retention_days = int(getattr(settings, "audit_retention_days", 90))

        self._queue: "asyncio.Queue[dict]" = asyncio.Queue(maxsize=10_000)
        self._task: Optional[asyncio.Task] = None
        self._task_retention: Optional[asyncio.Task] = None
        self._repo = AuditLogRepositoryImpl()

    async def start(self):
        if not self.enabled:
            return
        self._task = asyncio.create_task(self._consumer(), name="audit-consumer")
        self._task_retention = asyncio.create_task(self._retention_worker(), name="audit-retention")

    async def stop(self):
        if not self.enabled:
            return
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
            self._task = None
        if self._task_retention:
            self._task_retention.cancel()
            try: await self._task_retention
            except asyncio.CancelledError: pass
            self._task_retention = None
        # flush remaining
        await self._flush_remaining()

    async def log(self, *, user_id: Optional[UUID], action: str, resource: str,
                  ip: Optional[str], ua: Optional[str], meta: Optional[Dict[str, Any]] = None):
        if not self.enabled:
            return
        try:
            payload = {
                "user_id": user_id,
                "action": action[:64],
                "resource": resource[:128],
                "ip": (ip or "")[:45] or None,
                "ua": (ua or "")[:255] or None,
                "created_at": datetime.utcnow(),
                "meta": _mask_meta(meta),
            }
            self._queue.put_nowait(payload)
        except asyncio.QueueFull:
            # queue saturée: on droppe silencieusement (ou log) pour ne pas impacter les requêtes
            pass

    async def _consumer(self):
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception:
                # en cas d'erreur transitoire: on réessaie au tick suivant
                continue

    async def _flush_batch(self):
        rows = []
        while len(rows) < self.batch_size and not self._queue.empty():
            rows.append(self._queue.get_nowait())
        if not rows:
            return
        async with async_session_maker() as db:
            await self._repo.bulk_insert(db, rows)

    async def _flush_remaining(self):
        rows = []
        while not self._queue.empty():
            rows.append(self._queue.get_nowait())
            if len(rows) >= self.batch_size:
                async with async_session_maker() as db:
                    await self._repo.bulk_insert(db, rows)
                rows = []
        if rows:
            async with async_session_maker() as db:
                await self._repo.bulk_insert(db, rows)

    async def _retention_worker(self):
        # purge quotidienne
        while True:
            try:
                await asyncio.sleep(24 * 3600)
                cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
                async with async_session_maker() as db:
                    await self._repo.delete_older_than(db, before=cutoff)
            except asyncio.CancelledError:
                break
            except Exception:
                continue

audit_logger = AuditLogger()
