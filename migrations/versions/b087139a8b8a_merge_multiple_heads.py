"""merge_multiple_heads

Revision ID: b087139a8b8a
Revises: add_org_id_to_expense, ae96d2da8346
Create Date: 2024-10-31 17:08:41.589838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b087139a8b8a'
down_revision = ('add_org_id_to_expense', 'ae96d2da8346')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
