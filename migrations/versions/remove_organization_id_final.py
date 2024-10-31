"""remove organization_id from expense table

Revision ID: remove_organization_id_final
Revises: 
Create Date: 2024-10-31 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_organization_id_final'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Remove the organization_id column and its foreign key constraint
    with op.batch_alter_table('expense') as batch_op:
        batch_op.drop_constraint('fk_expense_organization_final', type_='foreignkey')
        batch_op.drop_column('organization_id')

def downgrade():
    # Add back the organization_id column and its foreign key constraint
    op.add_column('expense',
        sa.Column('organization_id', sa.Integer(), nullable=True)
    )
    
    # Update organization_id based on user's organization
    connection = op.get_bind()
    connection.execute(text('''
        UPDATE expense 
        SET organization_id = u.organization_id 
        FROM "user" u
        WHERE expense.user_id = u.id
    '''))
    
    # Make the column not nullable and add foreign key
    op.alter_column('expense', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    op.create_foreign_key(
        'fk_expense_organization_final',
        'expense', 'organization',
        ['organization_id'], ['id']
    )
