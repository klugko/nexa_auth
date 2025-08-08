"""RBAC: roles + user_roles; seed initial roles"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250808_rbac"
down_revision = None  # ou mets l'ID de la dernière migration existante
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    # seed initial
    roles_table = sa.table(
        "roles",
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(roles_table, [
        {"name": "admin",   "description": "Administrator"},
        {"name": "manager", "description": "Manager"},
        {"name": "user",    "description": "Regular user"},
    ])

def downgrade():
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_table("roles")
