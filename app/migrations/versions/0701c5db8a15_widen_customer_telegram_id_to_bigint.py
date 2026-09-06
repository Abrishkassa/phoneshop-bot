"""widen customer_telegram_id to bigint

Revision ID: 0701c5db8a15
Revises: c469847ac6ce
Create Date: 2026-09-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0701c5db8a15"
down_revision = "c469847ac6ce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "inquiries",
        "customer_telegram_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "inquiries",
        "customer_telegram_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )