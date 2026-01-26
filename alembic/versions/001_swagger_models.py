"""Add new models for Swagger alignment

Revision ID: 001_swagger_models
Revises: 
Create Date: 2026-01-26 16:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_swagger_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema."""
    
    # Update users table
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('avatar', sa.String(), nullable=True))
    op.add_column('users', sa.Column('settings', sa.JSON(), nullable=True))
    
    # Update materials table
    op.add_column('materials', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('materials', sa.Column('upload_date', sa.DateTime(), nullable=True))
    op.add_column('materials', sa.Column('status', sa.String(), nullable=True, server_default='processing'))
    op.add_column('materials', sa.Column('course_id', sa.String(), nullable=True))
    
    # Create ai_sessions table
    op.create_table(
        'ai_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(), nullable=False, server_default='New Chat'),
        sa.Column('doc_id', sa.String(36), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('messages', sa.JSON(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ocr_results table
    op.create_table(
        'ocr_results',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('student_name', sa.String(), nullable=False),
        sa.Column('student_accuracy', sa.Integer(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('questions', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('manual_score', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create public_links table
    op.create_table(
        'public_links',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('short_code', sa.String(), nullable=False),
        sa.Column('view_only', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_copy', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('password', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on short_code for fast lookups
    op.create_index('ix_public_links_short_code', 'public_links', ['short_code'], unique=True)


def downgrade():
    """Downgrade database schema."""
    
    # Drop new tables
    op.drop_index('ix_public_links_short_code', table_name='public_links')
    op.drop_table('public_links')
    op.drop_table('ocr_results')
    op.drop_table('ai_sessions')
    
    # Remove columns from materials
    op.drop_column('materials', 'course_id')
    op.drop_column('materials', 'status')
    op.drop_column('materials', 'upload_date')
    op.drop_column('materials', 'content')
    
    # Remove columns from users
    op.drop_column('users', 'settings')
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
