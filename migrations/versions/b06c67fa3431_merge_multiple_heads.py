"""merge multiple heads

Revision ID: b06c67fa3431
Revises: add_organization_id_to_expense_category
Create Date: 2024-10-31 16:46:26.125919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b06c67fa3431'
down_revision = 'add_organization_id_to_expense_category'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
