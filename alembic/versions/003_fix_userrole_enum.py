"""Fix userrole enum values

Revision ID: 003
Revises: 002
Create Date: 2026-02-02 23:47:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_fix_userrole_enum'
down_revision = '002_add_student_role'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add lowercase values if they don't exist
    # Using connection to commit after each ALTER TYPE
    connection = op.get_bind()
    
    connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'teacher'"))
    connection.commit()
    
    connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'"))
    connection.commit()
    
    connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'student'"))
    connection.commit()
    
    # Step 2: Update existing records to use lowercase values
    op.execute("UPDATE users SET role = 'teacher' WHERE role = 'TEACHER'")
    op.execute("UPDATE users SET role = 'admin' WHERE role = 'ADMIN'")
    op.execute("UPDATE users SET role = 'student' WHERE role = 'STUDENT'")


def downgrade():
    # Update records back to uppercase
    op.execute("UPDATE users SET role = 'TEACHER' WHERE role = 'teacher'")
    op.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'STUDENT' WHERE role = 'student'")
