from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0008_metrics_tables'
down_revision = '0007_sync_etags_and_stamps'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'session_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('planned_minutes', sa.Integer(), nullable=False),
        sa.Column('actual_minutes', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('course_label', sa.String(), nullable=True),
        sa.Column('logged_at', sa.String(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('session_log_type_course_idx', 'session_log', ['type', 'course_label'])


def downgrade():
    op.drop_index('session_log_type_course_idx', table_name='session_log')
    op.drop_table('session_log')
