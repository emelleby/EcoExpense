"""merge multiple heads

Revision ID: 4718e0bfa470
Revises: 99633c5183d9, a3b50c12eb43
Create Date: 2024-10-27 01:22:02.330001

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4718e0bfa470'
down_revision = ('99633c5183d9', 'a3b50c12eb43')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
