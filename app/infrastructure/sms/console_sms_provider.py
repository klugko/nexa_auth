from app.infrastructure.sms.sms_provider import SmsProvider

class ConsoleSmsProvider(SmsProvider):
    async def send(self, to: str, message: str) -> None:
        # Dev only
        print(f"[SMS -> {to}] {message}")
