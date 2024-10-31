"""add_kwh_column_to_expense_model

Revision ID: 46599494ecce
Revises: 943df735f8c8
Create Date: 2024-10-31 10:02:14.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '46599494ecce'
down_revision = '943df735f8c8'
branch_labels = None
depends_on = None

def upgrade():
    # Add column as nullable first
    op.add_column('expense', sa.Column('kwh', sa.Float(), nullable=True))
    
    # Update existing records with default value
    op.execute('UPDATE expense SET kwh = 0.0 WHERE kwh IS NULL')
    
    # Add NOT NULL constraint
    op.alter_column('expense', 'kwh',
                    existing_type=sa.Float(),
                    nullable=False,
                    server_default='0.0')

def downgrade():
    op.drop_column('expense', 'kwh')
