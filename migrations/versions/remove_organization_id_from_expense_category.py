"""remove_organization_id_from_expense_category

Revision ID: remove_organization_id
Revises: 9fefc5ce462b
Create Date: 2024-10-31 17:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_organization_id'
down_revision = '9fefc5ce462b'
branch_labels = None
depends_on = None

def upgrade():
    # Remove organization_id column and foreign key
    with op.batch_alter_table('expense_category') as batch_op:
        batch_op.drop_constraint('expense_category_organization_id_fkey', type_='foreignkey')
        batch_op.drop_column('organization_id')
        # Drop old unique constraint and create new one
        batch_op.drop_constraint('_name_org_uc', type_='unique')
        batch_op.create_unique_constraint('_name_uc', ['name'])

def downgrade():
    # Add back organization_id column and foreign key
    with op.batch_alter_table('expense_category') as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('expense_category_organization_id_fkey', 'organization', ['organization_id'], ['id'])
        # Drop new unique constraint and create old one
        batch_op.drop_constraint('_name_uc', type_='unique')
        batch_op.create_unique_constraint('_name_org_uc', ['name', 'organization_id'])
