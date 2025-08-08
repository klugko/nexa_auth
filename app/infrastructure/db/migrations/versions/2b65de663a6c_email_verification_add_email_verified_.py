"""email verification: add email_verified to users and create email_verification_tokens

Revision ID: 2b65de663a6c
Revises: c29f3903e121
Create Date: 2025-08-08 19:57:00.162912
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2b65de663a6c"
down_revision: Union[str, Sequence[str], None] = "c29f3903e121"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Ajouter la colonne en nullable + server_default=false (remplit false pour les rows existantes)
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=True, server_default=sa.text("false")),
    )

    # 2) Créer la table email_verification_tokens (si pas déjà créée)
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hashed_token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_email_verif_tokens_user_id", "email_verification_tokens", ["user_id"])
    op.create_index("ix_email_verif_tokens_hashed_token", "email_verification_tokens", ["hashed_token"], unique=True)

    # 3) Retirer le server_default (optionnel) pour garder la maîtrise côté app
    op.alter_column(
        "users",
        "email_verified",
        server_default=None,
        existing_type=sa.Boolean(),
        existing_nullable=True,
    )

    # 4) Rendre NOT NULL maintenant que toutes les lignes ont une valeur
    op.alter_column(
        "users",
        "email_verified",
        nullable=False,
        existing_type=sa.Boolean(),
    )


def downgrade() -> None:
    op.drop_index("ix_email_verif_tokens_hashed_token", table_name="email_verification_tokens")
    op.drop_index("ix_email_verif_tokens_user_id", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_column("users", "email_verified")
