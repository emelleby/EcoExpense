"""merge_multiple_heads

Revision ID: d27aa92ad0bf
Revises: add_organization_id_to_expense
Create Date: 2024-10-31 17:59:29.938049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd27aa92ad0bf'
down_revision = 'add_organization_id_to_expense'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
