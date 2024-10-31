"""final migration fix all tables

Revision ID: final_migration_fix_all
Revises: 
Create Date: 2024-10-31 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'final_migration_fix_all'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add organization_id to supplier if it doesn't exist
    try:
        op.add_column('supplier', sa.Column('organization_id', sa.Integer(), nullable=True))
        
        # Update existing suppliers with organization_id from their expenses' users
        connection = op.get_bind()
        connection.execute(text('''
            UPDATE supplier 
            SET organization_id = (
                SELECT DISTINCT u.organization_id 
                FROM expense e 
                JOIN "user" u ON e.user_id = u.id 
                WHERE e.supplier_id = supplier.id
                LIMIT 1
            )
            WHERE organization_id IS NULL
        '''))
        
        # Make supplier.organization_id not nullable
        op.alter_column('supplier', 'organization_id',
                       existing_type=sa.Integer(),
                       nullable=False)
        
        # Add foreign key for supplier.organization_id
        op.create_foreign_key(
            'fk_supplier_organization',
            'supplier', 'organization',
            ['organization_id'], ['id']
        )
    except Exception:
        pass  # Column might already exist

    # Handle expense table organization_id
    try:
        op.add_column('expense', sa.Column('organization_id', sa.Integer(), nullable=True))
        
        # Update existing expenses with organization_id from their users
        connection = op.get_bind()
        connection.execute(text('''
            UPDATE expense 
            SET organization_id = u.organization_id 
            FROM "user" u
            WHERE expense.user_id = u.id
            AND expense.organization_id IS NULL
        '''))
        
        # Make expense.organization_id not nullable
        op.alter_column('expense', 'organization_id',
                       existing_type=sa.Integer(),
                       nullable=False)
        
        # Add foreign key for expense.organization_id
        op.create_foreign_key(
            'fk_expense_organization',
            'expense', 'organization',
            ['organization_id'], ['id']
        )
    except Exception:
        pass  # Column might already exist

def downgrade():
    # Remove constraints and columns in reverse order
    try:
        op.drop_constraint('fk_expense_organization', 'expense', type_='foreignkey')
        op.drop_column('expense', 'organization_id')
        op.drop_constraint('fk_supplier_organization', 'supplier', type_='foreignkey')
        op.drop_column('supplier', 'organization_id')
    except Exception:
        pass
