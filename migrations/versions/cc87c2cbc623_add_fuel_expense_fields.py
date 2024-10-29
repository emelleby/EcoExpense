"""add fuel expense fields

Revision ID: cc87c2cbc623
Revises: 99633c5183d9
Create Date: 2024-10-29 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc87c2cbc623'
down_revision = '99633c5183d9'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_fuel column to expense_category table
    with op.batch_alter_table('expense_category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_fuel', sa.Boolean(), nullable=False, server_default='false'))

    # Add fuel expense specific fields to expense table
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.add_column(sa.Column('kilometers', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('fuel_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('fuel_amount_liters', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('co2_emissions', sa.Float(), nullable=True))


def downgrade():
    # Remove fuel expense specific fields from expense table
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.drop_column('co2_emissions')
        batch_op.drop_column('fuel_amount_liters')
        batch_op.drop_column('fuel_type')
        batch_op.drop_column('kilometers')

    # Remove is_fuel column from expense_category table
    with op.batch_alter_table('expense_category', schema=None) as batch_op:
        batch_op.drop_column('is_fuel')
