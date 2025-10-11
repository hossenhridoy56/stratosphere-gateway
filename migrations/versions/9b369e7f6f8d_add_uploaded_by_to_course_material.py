"""Add uploaded_by to course_material

Revision ID: 9b369e7f6f8d
Revises: 8ac0443aa247
Create Date: 2025-10-10 15:30:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9b369e7f6f8d'
down_revision = '8ac0443aa247'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('course_material', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uploaded_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_course_material_uploaded_by_teacher',  # ✅ Named constraint
            'teacher',  # ✅ Referenced table
            ['uploaded_by'],  # ✅ Local column
            ['id']  # ✅ Remote column
        )

def downgrade():
    with op.batch_alter_table('course_material', schema=None) as batch_op:
        batch_op.drop_constraint('fk_course_material_uploaded_by_teacher', type_='foreignkey')
        batch_op.drop_column('uploaded_by')