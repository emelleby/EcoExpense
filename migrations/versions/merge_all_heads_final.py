"""merge all heads final

Revision ID: merge_all_heads_final
Revises: add_organization_id_final, remove_organization_id
Create Date: 2024-10-31 18:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_all_heads_final'
down_revision = None
branch_labels = None
depends_on = ['add_organization_id_final', 'remove_organization_id']

def upgrade():
    pass

def downgrade():
    pass
