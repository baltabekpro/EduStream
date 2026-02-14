"""Merge course-related 004 heads

Revision ID: 005_merge_course_heads
Revises: 004_add_course_model, 004_add_courses_and_quiz_title
Create Date: 2026-02-14 18:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '005_merge_course_heads'
down_revision = ('004_add_course_model', '004_add_courses_and_quiz_title')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
