"""update_organization_regnr_field

Revision ID: 73dc364f1fa8
Revises: 379eb7fad554
Create Date: 2024-11-04 09:15:18.336978

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73dc364f1fa8'
down_revision = '379eb7fad554'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('organization', schema=None) as batch_op:
        batch_op.alter_column('regnr',
               existing_type=sa.VARCHAR(length=9),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('organization', schema=None) as batch_op:
        batch_op.alter_column('regnr',
               existing_type=sa.VARCHAR(length=9),
               nullable=True)

    # ### end Alembic commands ###
