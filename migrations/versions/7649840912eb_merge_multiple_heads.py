"""merge multiple heads

Revision ID: 7649840912eb
Revises: 34d15d5232c4, 98680feabe05
Create Date: 2024-10-30 10:03:26.650247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7649840912eb'
down_revision = ('34d15d5232c4', '98680feabe05')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
