"""Add user_id to Trip and Project models

Revision ID: 99633c5183d9
Revises: 71caf8fee5d9
Create Date: 2024-10-27 00:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99633c5183d9'
down_revision = '71caf8fee5d9'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection
    connection = op.get_bind()
    
    # Add user_id columns as nullable first
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_trip_user_id', 'user', ['user_id'], ['id'])

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_project_user_id', 'user', ['user_id'], ['id'])

    # Get first admin user's id
    admin_user = connection.execute(sa.text("SELECT id FROM \"user\" WHERE is_admin = true LIMIT 1")).fetchone()
    if admin_user:
        admin_id = admin_user[0]
        # Set default user_id for existing records
        connection.execute(sa.text(f"UPDATE trip SET user_id = {admin_id} WHERE user_id IS NULL"))
        connection.execute(sa.text(f"UPDATE project SET user_id = {admin_id} WHERE user_id IS NULL"))

        # Add NOT NULL constraint
        with op.batch_alter_table('trip', schema=None) as batch_op:
            batch_op.alter_column('user_id', nullable=False)

        with op.batch_alter_table('project', schema=None) as batch_op:
            batch_op.alter_column('user_id', nullable=False)


def downgrade():
    # Remove foreign key constraints and columns
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.drop_constraint('fk_trip_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_constraint('fk_project_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
