"""add_organization_id_to_expense_category

Revision ID: add_organization_id_to_expense_category
Revises: cae18d37f830
Create Date: 2024-10-31 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_organization_id_to_expense_category'
down_revision = 'cae18d37f830'
branch_labels = None
depends_on = None

def upgrade():
    # Add organization_id column
    op.add_column('expense_category', sa.Column('organization_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_expense_category_organization',
        'expense_category', 'organization',
        ['organization_id'], ['id']
    )
    
    # Make the column not nullable after adding the constraint
    op.alter_column('expense_category', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=False)

def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_expense_category_organization', 'expense_category', type_='foreignkey')
    
    # Remove column
    op.drop_column('expense_category', 'organization_id')
