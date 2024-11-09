"""Make trip_id required in expenses

Revision ID: 3d2ce2907e96
Revises: ec58318e7a85
Create Date: 2024-11-09 12:02:11.797659

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d2ce2907e96'
down_revision = 'ec58318e7a85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.alter_column('trip_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.alter_column('trip_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###
