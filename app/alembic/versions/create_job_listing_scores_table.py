"""create job listing scores table

Revision ID: f753b352e257
Revises: e753b352e256
Create Date: 2024-03-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f753b352e257'
down_revision: Union[str, None] = 'e753b352e256'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create job_listing_scores table
    op.create_table(
        'job_listing_scores',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, default=0),
        sa.Column('trace', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('job_id', 'listing_id')
    )
    
    # Only index job_id since we query by job
    op.create_index('idx_job_listing_scores_job_id', 'job_listing_scores', ['job_id'])
    
    # Drop old columns
    op.drop_column('jobs', 'listing_scores')
    op.drop_column('listings', 'score')
    op.drop_column('listings', 'trace')


def downgrade() -> None:
    # Add back old columns
    op.add_column('jobs', sa.Column('listing_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('listings', sa.Column('score', sa.Integer(), nullable=True))
    op.add_column('listings', sa.Column('trace', sa.String(), nullable=True))
    
    # Drop new table and indexes
    op.drop_index('idx_job_listing_scores_job_id', 'job_listing_scores')
    op.drop_table('job_listing_scores') 