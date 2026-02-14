"""add_course_model_and_update_relationships

Revision ID: 004_add_course_model
Revises: 003_fix_userrole_enum
Create Date: 2026-02-09 12:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '004_add_course_model'
down_revision = '003_fix_userrole_enum'
branch_labels = None
depends_on = None


def get_uuid_type():
    """Platform-independent UUID type."""
    try:
        # Try PostgreSQL UUID
        return postgresql.UUID(as_uuid=True)
    except:
        # Fallback to String for SQLite
        return sa.String(36)


def upgrade() -> None:
    # Create courses table
    op.create_table('courses',
        sa.Column('id', get_uuid_type(), nullable=False),
        sa.Column('user_id', get_uuid_type(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add updated_at to materials table if not exists
    with op.batch_alter_table('materials', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        except:
            pass  # Column might already exist
    
    # Temporarily allow NULL for course_id during migration
    # This will be set properly after creating courses
    
    # Update materials table - rename old course_id to course_id_old temporarily
    with op.batch_alter_table('materials', schema=None) as batch_op:
        try:
            batch_op.alter_column('course_id', new_column_name='course_id_old', existing_type=sa.String())
        except:
            pass  # If column doesn't exist, skip
    
    # Add new course_id as UUID with foreign key
    with op.batch_alter_table('materials', schema=None) as batch_op:
        batch_op.add_column(sa.Column('course_id', get_uuid_type(), nullable=True))
        batch_op.create_foreign_key('fk_materials_course_id', 'courses', ['course_id'], ['id'], ondelete='SET NULL')
    
    # Update ocr_results table
    with op.batch_alter_table('ocr_results', schema=None) as batch_op:
        try:
            # Rename old course_id
            batch_op.alter_column('course_id', new_column_name='course_id_old', existing_type=sa.String())
        except:
            pass
        
        # Add new course_id as UUID
        batch_op.add_column(sa.Column('course_id', get_uuid_type(), nullable=True))
        batch_op.create_foreign_key('fk_ocr_results_course_id', 'courses', ['course_id'], ['id'], ondelete='SET NULL')
    
    # Migration of data will happen via Python script or API
    # Old string course_id values will be converted to Course objects


def downgrade() -> None:
    # Restore old course_id columns as strings
    with op.batch_alter_table('ocr_results', schema=None) as batch_op:
        batch_op.drop_constraint('fk_ocr_results_course_id', type_='foreignkey')
        batch_op.drop_column('course_id')
        try:
            batch_op.alter_column('course_id_old', new_column_name='course_id', existing_type=sa.String())
        except:
            pass
    
    with op.batch_alter_table('materials', schema=None) as batch_op:
        batch_op.drop_constraint('fk_materials_course_id', type_='foreignkey')
        batch_op.drop_column('course_id')
        try:
            batch_op.alter_column('course_id_old', new_column_name='course_id', existing_type=sa.String())
        except:
            pass
    
    op.drop_table('courses')
