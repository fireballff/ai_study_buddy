from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'app_meta',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('value', sa.String(255), nullable=False),
    )

def downgrade():
    op.drop_table('app_meta')