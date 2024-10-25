"""Add organization and role models

Revision ID: a3b50c12eb43
Revises: 71caf8fee5d9
Create Date: 2024-10-25 08:05:09.905038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3b50c12eb43'
down_revision = '71caf8fee5d9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('role_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))
        batch_op.create_foreign_key(None, 'role', ['role_id'], ['id'])
        batch_op.create_foreign_key(None, 'organization', ['organization_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('is_admin')
        batch_op.drop_column('role_id')
        batch_op.drop_column('organization_id')

    # ### end Alembic commands ###