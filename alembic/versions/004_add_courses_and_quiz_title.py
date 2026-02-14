"""Add courses table and quiz title

Revision ID: 004_add_courses_and_quiz_title
Revises: 003_fix_userrole_enum
Create Date: 2026-02-14 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_courses_and_quiz_title'
down_revision = '003_fix_userrole_enum'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = inspector.get_table_names()
    if 'courses' not in table_names:
        op.create_table(
            'courses',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('color', sa.String(), nullable=True),
            sa.Column('icon', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    quiz_columns = {col['name'] for col in inspector.get_columns('quizzes')}
    if 'title' not in quiz_columns:
        op.add_column('quizzes', sa.Column('title', sa.String(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    quiz_columns = {col['name'] for col in inspector.get_columns('quizzes')}
    if 'title' in quiz_columns:
        op.drop_column('quizzes', 'title')

    table_names = inspector.get_table_names()
    if 'courses' in table_names:
        op.drop_table('courses')
