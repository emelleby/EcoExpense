"""add organization_id to expense table

Revision ID: add_organization_id_to_expense
Revises: ff120b81eba9
Create Date: 2024-10-31 17:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_organization_id_to_expense'
down_revision = 'ff120b81eba9'
branch_labels = None
depends_on = None

def upgrade():
    # Add organization_id column
    op.add_column('expense', sa.Column('organization_id', sa.Integer(), nullable=True))
    
    # Update existing expenses with organization_id from their users
    connection = op.get_bind()
    connection.execute(text('''
        UPDATE expense 
        SET organization_id = u.organization_id 
        FROM "user" u
        WHERE expense.user_id = u.id
    '''))
    
    # Add foreign key constraint and make column not nullable
    op.alter_column('expense', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    op.create_foreign_key(
        'fk_expense_organization',
        'expense', 'organization',
        ['organization_id'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_expense_organization', 'expense', type_='foreignkey')
    op.drop_column('expense', 'organization_id')
