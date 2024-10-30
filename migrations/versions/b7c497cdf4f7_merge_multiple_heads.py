"""merge multiple heads

Revision ID: b7c497cdf4f7
Revises: 7eaac532a8da, 91884830808c
Create Date: 2024-10-30 09:58:48.970477

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c497cdf4f7'
down_revision = ('7eaac532a8da', '91884830808c')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
