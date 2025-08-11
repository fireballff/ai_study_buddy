from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_app_owned_event_meta'
down_revision = '0004_planner_prefs_and_blocks'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('events') as batch:
        batch.add_column(sa.Column('app_owned', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('app_tag', sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table('events') as batch:
        batch.drop_column('app_tag')
        batch.drop_column('app_owned')
