"""merge heads

Revision ID: merge_heads
Revises: 71caf8fee5d9, add_admin_users
Create Date: 2024-10-25 08:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = ('71caf8fee5d9', 'add_admin_users')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
