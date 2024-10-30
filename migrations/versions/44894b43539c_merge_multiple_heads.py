"""merge multiple heads

Revision ID: 44894b43539c
Revises: 769eef8384a4, fcc07e943352
Create Date: 2024-10-30 10:18:07.458215

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44894b43539c'
down_revision = ('769eef8384a4', 'fcc07e943352')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
