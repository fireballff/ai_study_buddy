from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0003_task_fields_and_indexes'
down_revision = '0002_smart_task_integration'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('tasks')}
    with op.batch_alter_table('tasks') as batch:
        if 'course_label' not in columns:
            batch.add_column(sa.Column('course_label', sa.String(), nullable=True))
        if 'priority' not in columns:
            batch.add_column(sa.Column('priority', sa.Integer(), nullable=True))
        if 'created_by' not in columns:
            batch.add_column(sa.Column('created_by', sa.String(), nullable=True, server_default='user'))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_course ON tasks(course_label)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)"))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('tasks')}
    with op.batch_alter_table('tasks') as batch:
        if 'created_by' in columns:
            batch.drop_column('created_by')
        if 'priority' in columns:
            batch.drop_column('priority')
        if 'course_label' in columns:
            batch.drop_column('course_label')
    op.execute(text("DROP INDEX IF EXISTS idx_tasks_course"))
    op.execute(text("DROP INDEX IF EXISTS idx_tasks_priority"))
    op.execute(text("DROP INDEX IF EXISTS idx_tasks_due"))
