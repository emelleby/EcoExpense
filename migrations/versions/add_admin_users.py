"""Add admin status to users

Revision ID: add_admin_users
Revises: 71caf8fee5d9
Create Date: 2024-10-25 08:14:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_admin_users'
down_revision = '71caf8fee5d9'
branch_labels = None
depends_on = None

def upgrade():
    # Set is_admin=True for all existing users
    connection = op.get_bind()
    connection.execute(text("UPDATE \"user\" SET is_admin = TRUE"))

def downgrade():
    # Set is_admin=False for all users
    connection = op.get_bind()
    connection.execute(text("UPDATE \"user\" SET is_admin = FALSE"))
