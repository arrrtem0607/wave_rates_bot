"""add usdt rates

Revision ID: 5a8b65b7d8d4
Revises: 31208e7daede
Create Date: 2025-05-24 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a8b65b7d8d4"
down_revision: Union[str, None] = "31208e7daede"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rates",
        sa.Column("usdt_rub_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "rates",
        sa.Column("usdt_rub_plus1_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        "UPDATE rates SET usdt_rub_cents = ust_rub_cents, usdt_rub_plus1_cents = ust_rub_plus1_cents"
    )
    op.alter_column("rates", "usdt_rub_cents", server_default=None)
    op.alter_column("rates", "usdt_rub_plus1_cents", server_default=None)


def downgrade() -> None:
    op.drop_column("rates", "usdt_rub_plus1_cents")
    op.drop_column("rates", "usdt_rub_cents")
