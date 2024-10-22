"""Increase password_hash length and update expense table

Revision ID: 58132c21f6ff
Revises: 
Create Date: 2024-10-22 08:46:02.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58132c21f6ff'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Increase password_hash length in the user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=255),
               existing_nullable=True)

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

    # Revert password_hash length in the user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True)
