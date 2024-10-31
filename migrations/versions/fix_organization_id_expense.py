"""Fix organization_id column in expense table

Revision ID: fix_organization_id_expense
Revises: 
Create Date: 2024-10-31 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_organization_id_expense'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add organization_id column if it doesn't exist
    op.add_column('expense', sa.Column('organization_id', sa.Integer(), nullable=True))
    
    # Update existing rows to use user's organization_id
    op.execute("""
        UPDATE expense 
        SET organization_id = (
            SELECT organization_id 
            FROM "user" 
            WHERE "user".id = expense.user_id
        )
    """)
    
    # Make organization_id not nullable after updating
    op.alter_column('expense', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(None, 'expense', 'organization', ['organization_id'], ['id'])

def downgrade():
    op.drop_constraint(None, 'expense', type_='foreignkey')
    op.drop_column('expense', 'organization_id')
