from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_smart_task_integration'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('start_time', sa.String(), nullable=False),
        sa.Column('end_time', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False, server_default=''),
    )
    op.create_index('events_source_idx', 'events', ['source', 'source_id'], unique=True)

    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('estimated_duration', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.String()),
        sa.Column('course_label', sa.String()),
        sa.Column('created_at', sa.String(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.String(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('start_time', sa.String()),
        sa.Column('end_time', sa.String()),
        sa.Column('state', sa.String(), nullable=False, server_default='pending'),
    )

    op.create_table(
        'staging_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('start_time', sa.String(), nullable=False),
        sa.Column('end_time', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False, server_default=''),
        sa.Column('updated_at', sa.String(), nullable=False),
    )

    op.create_table(
        'sync_cursors',
        sa.Column('provider', sa.String(), primary_key=True),
        sa.Column('cursor', sa.String(), nullable=False),
    )


def downgrade():
    op.drop_table('sync_cursors')
    op.drop_table('staging_events')
    op.drop_table('tasks')
    op.drop_index('events_source_idx', table_name='events')
    op.drop_table('events')
