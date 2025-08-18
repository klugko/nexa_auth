from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import différé pour éviter les imports circulaires
import importlib

entities_to_import = [
    "app.domain.entities.user",
    "app.domain.entities.auth_provider",
    "app.domain.entities.black_listed_token",
]

for entity_module in entities_to_import:
    importlib.import_module(entity_module)