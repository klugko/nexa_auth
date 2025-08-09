"""phone otp: add verification_codes + users.phone_verified

Revision ID: bf37d83ac15e
Revises: 0caf26a44aa5
Create Date: 2025-08-08 23:45:20.987939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf37d83ac15e'
down_revision: Union[str, Sequence[str], None] = '0caf26a44aa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    
def downgrade() -> None:
    op.drop_column('users', 'phone_verified')