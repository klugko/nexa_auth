from typing import Protocol

class SmsProvider(Protocol):
    async def send(self, to: str, message: str) -> None:
        ...
