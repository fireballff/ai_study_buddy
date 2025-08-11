from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0006_calendar_indexes'
down_revision = '0005_app_owned_event_meta'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_events_start_end ON events(start_time, end_time)"
        )
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_tasks_start_end ON tasks(start_time, end_time)"
        )
    )


def downgrade():
    op.execute(text("DROP INDEX IF EXISTS idx_events_start_end"))
    op.execute(text("DROP INDEX IF EXISTS idx_tasks_start_end"))
