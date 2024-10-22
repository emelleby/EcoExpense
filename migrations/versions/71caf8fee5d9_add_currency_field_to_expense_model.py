"""Add currency field to Expense model

Revision ID: 71caf8fee5d9
Revises: 58132c21f6ff
Create Date: 2024-10-22 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71caf8fee5d9'
down_revision = '58132c21f6ff'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to the expense table as nullable
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=True))
        batch_op.add_column(sa.Column('exchange_rate', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('nok_amount', sa.Float(), nullable=True))

    # Update existing rows with default values
    op.execute("UPDATE expense SET currency = 'NOK', exchange_rate = 1.0, nok_amount = amount WHERE currency IS NULL")

    # Add NOT NULL constraints
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.alter_column('currency', nullable=False)
        batch_op.alter_column('exchange_rate', nullable=False)
        batch_op.alter_column('nok_amount', nullable=False)


def downgrade():
    # Remove new columns from the expense table
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.drop_column('nok_amount')
        batch_op.drop_column('exchange_rate')
        batch_op.drop_column('currency')
