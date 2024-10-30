"""merge multiple heads

Revision ID: 82bc61ebd796
Revises: c78117176712, d9379fe7f03d
Create Date: 2024-10-30 10:30:47.608235

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82bc61ebd796'
down_revision = ('c78117176712', 'd9379fe7f03d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
