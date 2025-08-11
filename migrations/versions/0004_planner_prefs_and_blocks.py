from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0004_planner_prefs_and_blocks'
down_revision = '0003_task_fields_and_indexes'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'blocks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('start_time', sa.String(), nullable=False),
        sa.Column('end_time', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.CheckConstraint("kind IN ('busy','study_window')", name='blocks_kind_check'),
    )
    op.create_index('blocks_start_idx', 'blocks', ['start_time'])
    op.create_index('blocks_end_idx', 'blocks', ['end_time'])

    op.create_table(
        'prefs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('day_start', sa.String(), nullable=True),
        sa.Column('day_end', sa.String(), nullable=True),
        sa.Column('default_session_minutes', sa.Integer(), nullable=True),
        sa.Column('max_sessions_per_day', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_table('prefs')
    op.drop_index('blocks_end_idx', table_name='blocks')
    op.drop_index('blocks_start_idx', table_name='blocks')
    op.drop_table('blocks')
