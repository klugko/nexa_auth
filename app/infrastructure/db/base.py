from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import différé pour éviter les imports circulaires
import importlib

entities_to_import = [
    "app.domain.entities.user",
    "app.domain.entities.auth_provider",
    "app.domain.entities.black_listed_token",
    "app.domain.entities.password_reset_token",
    "app.domain.entities.role",
    "app.domain.entities.invitation",
    "app.domain.entities.verification_code",
    "app.domain.entities.user_resume",
    "app.domain.entities.user_skill",
    "app.domain.entities.user_score",
    "app.domain.entities.email_verification_token",
]

for entity_module in entities_to_import:
    importlib.import_module(entity_module)