from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0009_supabase_cache'
down_revision = '0008_metrics_tables'
branch_labels = None
depends_on = None


def upgrade():
    # tasks additional columns
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    task_cols = {c['name'] for c in inspector.get_columns('tasks')}
    with op.batch_alter_table('tasks', schema=None) as batch:
        if 'owner_user_id' not in task_cols:
            batch.add_column(sa.Column('owner_user_id', sa.String(), nullable=True))
        if 'source' not in task_cols:
            batch.add_column(sa.Column('source', sa.String(), nullable=False, server_default='app'))
        if 'source_id' not in task_cols:
            batch.add_column(sa.Column('source_id', sa.String(), nullable=False, server_default=''))
        if 'deleted_at' not in task_cols:
            batch.add_column(sa.Column('deleted_at', sa.String(), nullable=True))
        if 'version' not in task_cols:
            batch.add_column(sa.Column('version', sa.String(), nullable=False, server_default=''))
        if 'dirty' not in task_cols:
            batch.add_column(sa.Column('dirty', sa.Integer(), nullable=False, server_default='0'))
    op.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS tasks_src_idx ON tasks(owner_user_id, source, source_id)'))
    op.execute(text('CREATE INDEX IF NOT EXISTS tasks_state_due_idx ON tasks(owner_user_id, state, due_date)'))

    # events additional columns
    event_cols = {c['name'] for c in inspector.get_columns('events')}
    with op.batch_alter_table('events', schema=None) as batch:
        if 'owner_user_id' not in event_cols:
            batch.add_column(sa.Column('owner_user_id', sa.String(), nullable=True))
        if 'source' not in event_cols:
            batch.add_column(sa.Column('source', sa.String(), nullable=False, server_default='google'))
        if 'source_id' not in event_cols:
            batch.add_column(sa.Column('source_id', sa.String(), nullable=False, server_default=''))
        if 'etag' not in event_cols:
            batch.add_column(sa.Column('etag', sa.String(), nullable=True))
        if 'calendar_id' not in event_cols:
            batch.add_column(sa.Column('calendar_id', sa.String(), nullable=True))
        if 'deleted_at' not in event_cols:
            batch.add_column(sa.Column('deleted_at', sa.String(), nullable=True))
        if 'version' not in event_cols:
            batch.add_column(sa.Column('version', sa.String(), nullable=False, server_default=''))
        if 'dirty' not in event_cols:
            batch.add_column(sa.Column('dirty', sa.Integer(), nullable=False, server_default='0'))
    op.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS events_src_idx ON events(owner_user_id, source, source_id)'))
    op.execute(text('CREATE INDEX IF NOT EXISTS events_time_idx ON events(owner_user_id, start_time, end_time)'))

    # planner preferences
    op.create_table(
        'planner_prefs',
        sa.Column('owner_user_id', sa.String(), primary_key=True),
        sa.Column('focus_block_minutes', sa.Integer(), server_default='50'),
        sa.Column('break_minutes', sa.Integer(), server_default='10'),
        sa.Column('adhd_mode_enabled', sa.Boolean(), server_default='0'),
        sa.Column('dirty', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.String(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )

    # blocks
    if 'blocks' not in inspector.get_table_names():
        op.create_table(
            'blocks',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('owner_user_id', sa.String(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('start_time', sa.String(), nullable=False),
            sa.Column('end_time', sa.String(), nullable=False),
            sa.Column('dirty', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('updated_at', sa.String(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.execute(text('CREATE INDEX IF NOT EXISTS blocks_time_idx ON blocks(owner_user_id, start_time, end_time)'))
    else:
        op.execute(text('CREATE INDEX IF NOT EXISTS blocks_time_idx ON blocks(start_time, end_time)'))

    # sync state
    op.create_table(
        'sync_state',
        sa.Column('owner_user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('cursor', sa.String(), nullable=True),
        sa.Column('last_full_sync', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('owner_user_id', 'provider')
    )

    # pending ops
    op.create_table(
        'pending_ops',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('op_type', sa.String(), nullable=False),
        sa.Column('row_local_id', sa.String(), nullable=False),
        sa.Column('payload', sa.String(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade():
    op.drop_table('pending_ops')
    op.drop_table('sync_state')
    op.drop_index('blocks_time_idx', table_name='blocks')
    op.drop_table('blocks')
    op.drop_table('planner_prefs')
    with op.batch_alter_table('events', schema=None) as batch:
        batch.drop_column('dirty')
        batch.drop_column('version')
        batch.drop_column('deleted_at')
        batch.drop_column('calendar_id')
        batch.drop_column('etag')
        batch.drop_column('source_id')
        batch.drop_column('source')
        batch.drop_column('owner_user_id')
    with op.batch_alter_table('tasks', schema=None) as batch:
        batch.drop_column('dirty')
        batch.drop_column('version')
        batch.drop_column('deleted_at')
        batch.drop_column('source_id')
        batch.drop_column('source')
        batch.drop_column('owner_user_id')
