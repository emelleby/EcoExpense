"""final migration to fix all issues

Revision ID: final_migration_fix
Revises: 
Create Date: 2024-10-31 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'final_migration_fix'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create organization_id column if it doesn't exist
    try:
        op.add_column('expense', sa.Column('organization_id', sa.Integer(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    # Update existing expenses with organization_id from their users
    connection = op.get_bind()
    connection.execute(text('''
        UPDATE expense 
        SET organization_id = u.organization_id 
        FROM "user" u
        WHERE expense.user_id = u.id
        AND expense.organization_id IS NULL
    '''))
    
    # Make column not nullable
    op.alter_column('expense', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    # Add foreign key if it doesn't exist
    try:
        op.create_foreign_key(
            'fk_expense_organization_final',
            'expense', 'organization',
            ['organization_id'], ['id']
        )
    except Exception:
        pass  # Constraint might already exist

def downgrade():
    try:
        op.drop_constraint('fk_expense_organization_final', 'expense', type_='foreignkey')
        op.drop_column('expense', 'organization_id')
    except Exception:
        pass
