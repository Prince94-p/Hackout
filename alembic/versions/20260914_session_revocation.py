"""Persist per-session logout revocations."""
from alembic import op
import sqlalchemy as sa
revision = "20260914_sessions"
down_revision = "5c3e27a5863e"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("factories", sa.Column("request_key", sa.String(64), nullable=True))
    op.add_column("scenarios", sa.Column("request_key", sa.String(64), nullable=True))
    op.create_index("uq_factories_request_key", "factories", ["request_key"], unique=True)
    op.create_index("uq_scenarios_request_key", "scenarios", ["request_key"], unique=True)
    op.create_table("revoked_tokens", sa.Column("token_hash", sa.String(64), primary_key=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])

def downgrade():
    op.drop_index("uq_scenarios_request_key", table_name="scenarios")
    op.drop_index("uq_factories_request_key", table_name="factories")
    op.drop_column("scenarios", "request_key")
    op.drop_column("factories", "request_key")
    op.drop_table("revoked_tokens")
