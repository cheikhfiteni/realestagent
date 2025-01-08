"""add location fields to job templates

Revision ID: e753b352e256
Revises: d753b352e255
Create Date: 2024-01-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e753b352e256'
down_revision: Union[str, None] = 'd753b352e255'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add location-related columns
    op.add_column('job_templates', sa.Column('location', sa.String(), nullable=True))
    op.add_column('job_templates', sa.Column('zipcode', sa.String(), nullable=True))
    op.add_column('job_templates', sa.Column('search_distance_miles', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove location-related columns
    op.drop_column('job_templates', 'location')
    op.drop_column('job_templates', 'zipcode')
    op.drop_column('job_templates', 'search_distance_miles') 