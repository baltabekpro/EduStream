"""add_student_role

Revision ID: 002_add_student_role
Revises: 001_swagger_models
Create Date: 2026-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_student_role'
down_revision = '001_swagger_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'STUDENT' to the UserRole enum (uppercase to match existing values)
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'STUDENT'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values
    # This would require recreating the enum type
    pass
