"""create products and inquiries tables

Revision ID: c469847ac6ce
Revises:
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c469847ac6ce"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("brand", sa.String(length=60), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("colors", sa.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("stock_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("specs", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("photo_urls", sa.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inquiries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference_code", sa.String(length=10), nullable=False, unique=True),
        sa.Column("customer_telegram_id", sa.Integer(), nullable=False),
        sa.Column("customer_username", sa.String(length=60), nullable=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("preferred_color", sa.String(length=40), nullable=True),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inquiries_status", "inquiries", ["status"])
    op.create_index("ix_products_category", "products", ["category"])


def downgrade() -> None:
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_inquiries_status", table_name="inquiries")
    op.drop_table("inquiries")
    op.drop_table("products")
