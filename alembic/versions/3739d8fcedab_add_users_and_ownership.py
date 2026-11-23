"""add users and ownership

Revision ID: 3739d8fcedab
Revises: 950922842e72
Create Date: 2026-11-23 01:03:59.010545

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3739d8fcedab"
down_revision: str | Sequence[str] | None = "950922842e72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.add_column(
        "documents",
        sa.Column("owner_id", sa.Uuid(), nullable=True),
    )

    op.create_index(
        "ix_documents_owner_id",
        "documents",
        ["owner_id"],
    )

    op.create_foreign_key(
        "fk_documents_owner_id_users",
        "documents",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_conversations_owner_id",
        "conversations",
        ["owner_id"],
    )

    op.create_index(
        "ix_conversations_owner_updated",
        "conversations",
        ["owner_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversations_owner_updated",
        table_name="conversations",
    )
    op.drop_index(
        "ix_conversations_owner_id",
        table_name="conversations",
    )
    op.drop_table("conversations")

    op.drop_constraint(
        "fk_documents_owner_id_users",
        "documents",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_documents_owner_id",
        table_name="documents",
    )
    op.drop_column("documents", "owner_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
