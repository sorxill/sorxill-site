"""Начальная схема: проекты, переводы, пользователи, заявки, лента, аудит.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute("CREATE TYPE publish_status AS ENUM ('draft', 'published', 'archived')")
    op.execute("CREATE TYPE user_role AS ENUM ('owner', 'editor', 'viewer')")

    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="publish_status", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("cover_url", sa.Text()),
        sa.Column("repo_url", sa.Text()),
        sa.Column("live_url", sa.Text()),
        sa.Column(
            "stack", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Инварианты дублируются здесь и в домене: БД защищает от ошибок
        # миграций и ручных правок, домен даёт понятную ошибку пользователю.
        sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="projects_slug_format"),
        sa.CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL", name="published_requires_date"
        ),
        sa.CheckConstraint(
            "status <> 'published' OR cover_url IS NOT NULL", name="published_requires_cover"
        ),
    )
    op.execute(
        "CREATE INDEX projects_published_idx ON projects (sort_order DESC, published_at DESC) "
        "WHERE status = 'published'"
    )

    op.create_table(
        "project_translations",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("locale", sa.String(2), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False, server_default=""),
        sa.CheckConstraint("locale IN ('ru','en')", name="translations_locale"),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(name="user_role", create_type=False),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column("totp_secret", sa.Text()),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "contact_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ip_hash", sa.Text()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("is_spam", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("handled_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("length(body) BETWEEN 10 AND 5000", name="contact_body_length"),
    )
    op.execute("CREATE INDEX contact_created_idx ON contact_messages (created_at DESC)")

    op.create_table(
        "feed_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("source", sa.String(24), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("locale", sa.String(2)),
        sa.Column(
            "item_metrics", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index("feed_source_external_uq", "feed_items", ["source", "external_id"], unique=True)
    op.execute(
        "CREATE INDEX feed_visible_idx ON feed_items (occurred_at DESC) WHERE is_hidden = false"
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text()),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("feed_items")
    op.drop_table("contact_messages")
    op.drop_table("users")
    op.drop_table("project_translations")
    op.drop_table("projects")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS publish_status")
