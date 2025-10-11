"""Add composite unique constraint to course

Revision ID: a94afc66ceaa
Revises: fcce80ec6a41
Create Date: 2025-10-10 12:49:31.939223
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a94afc66ceaa'
down_revision = 'fcce80ec6a41'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.create_unique_constraint('unique_code_per_session', ['code', 'session'])

def downgrade():
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_constraint('unique_code_per_session', type_='unique')