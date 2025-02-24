"""Add employee old col

Revision ID: d6055983828c
Revises: e693fb61e43d
Create Date: 2025-01-29 11:22:55.103106

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd6055983828c'
down_revision: Union[str, None] = 'e693fb61e43d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('employees', sa.Column('employee_old_legal_person', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('employees', 'employee_old_legal_person')
    # ### end Alembic commands ###
