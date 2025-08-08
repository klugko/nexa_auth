from app.config import settings
from app.infrastructure.sms.console_sms_provider import ConsoleSmsProvider
from app.infrastructure.sms.sms_provider import SmsProvider

def get_sms_provider() -> SmsProvider:
    prov = (settings.__dict__.get("sms_provider") or "console").lower()
    # prêt pour twilio, etc. plus tard
    return ConsoleSmsProvider()
