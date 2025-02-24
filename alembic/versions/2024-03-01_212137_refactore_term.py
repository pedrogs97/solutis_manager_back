"""refactore term

Revision ID: 47d83a332341
Revises: 40da88cf4fbe
Create Date: 2024-03-01 21:21:37.883641

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "47d83a332341"
down_revision: Union[str, None] = "40da88cf4fbe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("asset_ibfk_2", "asset", type_="foreignkey")
    op.drop_table("asset_clothing_size")
    op.drop_column("asset", "clothing_size_id")
    op.drop_constraint("lending_ibfk_6", "lending", type_="foreignkey")
    op.drop_table("lending_type")
    op.drop_column("lending", "type_id")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lending_type",
        sa.Column("id", mysql.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", mysql.VARCHAR(length=40), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.add_column(
        "lending",
        sa.Column("type_id", mysql.INTEGER(), autoincrement=False, nullable=False),
    )
    op.create_foreign_key(
        "lending_ibfk_6", "lending", "lending_type", ["type_id"], ["id"]
    )
    op.create_table(
        "asset_clothing_size",
        sa.Column("id", mysql.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", mysql.VARCHAR(length=5), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.add_column(
        "asset",
        sa.Column(
            "clothing_size_id", mysql.INTEGER(), autoincrement=False, nullable=True
        ),
    )
    op.create_foreign_key(
        "asset_ibfk_2", "asset", "asset_clothing_size", ["clothing_size_id"], ["id"]
    )
    # ### end Alembic commands ###
