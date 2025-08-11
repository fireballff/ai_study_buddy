from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0007_sync_etags_and_stamps'
down_revision = '0006_calendar_indexes'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('events') as batch:
        batch.add_column(sa.Column('etag', sa.String(), nullable=True))
        batch.add_column(sa.Column('updated_at', sa.String(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        batch.add_column(sa.Column('last_synced_at', sa.String(), nullable=True))
    with op.batch_alter_table('staging_events') as batch:
        batch.add_column(sa.Column('etag', sa.String(), nullable=True))

def downgrade():
    with op.batch_alter_table('staging_events') as batch:
        batch.drop_column('etag')
    with op.batch_alter_table('events') as batch:
        batch.drop_column('last_synced_at')
        batch.drop_column('updated_at')
        batch.drop_column('etag')
