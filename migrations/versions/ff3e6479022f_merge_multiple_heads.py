"""merge multiple heads

Revision ID: ff3e6479022f
Revises: 94c527c4497c, cdc1e788b1fc
Create Date: 2024-10-29 15:16:52.053676

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff3e6479022f'
down_revision = ('94c527c4497c', 'cdc1e788b1fc')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
