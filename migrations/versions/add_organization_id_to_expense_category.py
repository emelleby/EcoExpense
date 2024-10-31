"""add_organization_id_to_expense_category

Revision ID: add_organization_id_to_expense_category
Revises: cae18d37f830
Create Date: 2024-10-31 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = 'add_organization_id_to_expense_category'
down_revision = 'cae18d37f830'
branch_labels = None
depends_on = None

def upgrade():
    # Add organization_id column as nullable first
    op.add_column('expense_category', sa.Column('organization_id', sa.Integer(), nullable=True))
    
    # Create a connection to execute SQL
    connection = op.get_bind()
    
    # Get the first organization's ID
    org_id = connection.execute("SELECT id FROM organization ORDER BY id LIMIT 1").scalar()
    
    if org_id is not None:
        # Update existing records to use the first organization's ID
        connection.execute(
            "UPDATE expense_category SET organization_id = %s WHERE organization_id IS NULL",
            (org_id,)
        )
    
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
