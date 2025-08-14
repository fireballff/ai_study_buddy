"""Sync metadata for events and staging events.

This migration is written to be *idempotent* and resilient to partially
applied previous attempts. SQLite requires batch mode for many schema
changes which creates temporary tables. Failed runs can leave those
temporary tables behind; the helper below ensures they are cleaned up
before proceeding.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_sync_etags_and_stamps"
down_revision = "0006_calendar_indexes"
branch_labels = None
depends_on = None


def _drop_sqlite_tmp_tables() -> None:
    """Remove leftover _alembic_tmp_* tables from failed batch migrations."""
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        return
    for tbl in ("_alembic_tmp_events", "_alembic_tmp_staging_events"):
        try:
            bind.execute(sa.text(f"DROP TABLE IF EXISTS {tbl}"))
        except Exception:  # pragma: no cover - defensive
            pass


def upgrade() -> None:
    _drop_sqlite_tmp_tables()
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # ------------------------------------------------------------------
    # Ensure staging_events table exists
    if not insp.has_table("staging_events"):
        op.create_table(
            "staging_events",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("source", sa.String(), nullable=False, server_default=""),
            sa.Column("source_id", sa.String(), nullable=False, server_default=""),
            sa.Column("payload", sa.Text(), nullable=False, server_default=""),
        )
        insp = sa.inspect(bind)

    st_cols = {c["name"] for c in insp.get_columns("staging_events")}
    with op.batch_alter_table("staging_events") as batch:
        if "etag" not in st_cols:
            batch.add_column(sa.Column("etag", sa.String()))
        if "sync_timestamp" not in st_cols:
            batch.add_column(sa.Column("sync_timestamp", sa.String()))

    # ------------------------------------------------------------------
    # Add sync metadata to events table
    ev_cols = {c["name"] for c in insp.get_columns("events")}
    needed = any(
        name not in ev_cols
        for name in ("etag", "updated_at", "last_synced_at", "app_owned", "app_tag")
    )
    if needed:
        with op.batch_alter_table("events") as batch:
            if "etag" not in ev_cols:
                batch.add_column(sa.Column("etag", sa.String()))
            if "updated_at" not in ev_cols:
                batch.add_column(
                    sa.Column(
                        "updated_at",
                        sa.String(),
                        nullable=False,
                        server_default=sa.text("CURRENT_TIMESTAMP"),
                    )
                )
            if "last_synced_at" not in ev_cols:
                batch.add_column(sa.Column("last_synced_at", sa.String()))
            if "app_owned" not in ev_cols:
                batch.add_column(
                    sa.Column("app_owned", sa.Integer(), nullable=False, server_default="0")
                )
            if "app_tag" not in ev_cols:
                batch.add_column(sa.Column("app_tag", sa.String()))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("staging_events"):
        st_cols = {c["name"] for c in insp.get_columns("staging_events")}
        with op.batch_alter_table("staging_events") as batch:
            if "sync_timestamp" in st_cols:
                batch.drop_column("sync_timestamp")
            if "etag" in st_cols:
                batch.drop_column("etag")

    if insp.has_table("events"):
        ev_cols = {c["name"] for c in insp.get_columns("events")}
        with op.batch_alter_table("events") as batch:
            for name in ["app_tag", "app_owned", "last_synced_at", "updated_at", "etag"]:
                if name in ev_cols:
                    batch.drop_column(name)
