"""add name column to jobs

Revision ID: d753b352e255
Revises: 
Create Date: 2024-12-20 06:04:44.633351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd753b352e255'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add column as nullable
    op.add_column('jobs', sa.Column('name', sa.String(), nullable=True))
    
    # Step 2: Set default value for existing rows
    op.execute("UPDATE jobs SET name = 'Unnamed Job' WHERE name IS NULL")
    
    # Step 3: Make it non-nullable
    op.alter_column('jobs', 'name',
                    existing_type=sa.String(),
                    nullable=False)


def downgrade() -> None:
    op.drop_column('jobs', 'name')
