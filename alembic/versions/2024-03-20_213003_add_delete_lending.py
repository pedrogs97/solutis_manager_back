"""add delete lending

Revision ID: 0bda80475419
Revises: a864fda63408
Create Date: 2024-03-20 21:30:03.934316

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0bda80475419"
down_revision: Union[str, None] = "a864fda63408"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("lending", sa.Column("deleted", sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("lending", "deleted")
