"""create_pipeline_watermarks_table

Revision ID: a1b2c3d4e5f6
Revises: 0d32f3ef9fd5
Create Date: 2026-09-22 18:28:00.000000

Creates the ``pipeline_watermarks`` table used by Part 9 incremental
processing to persist the composite high-water-mark state for each
incremental pipeline source.

The watermark is committed ONLY after successful curated persistence and
reconciliation.  A failed run leaves the committed watermark unchanged so
that the next run retries from the correct position.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '0d32f3ef9fd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the pipeline_watermarks table."""
    op.create_table(
        'pipeline_watermarks',
        sa.Column(
            'pipeline_key',
            sa.String(length=128),
            nullable=False,
            comment=(
                "Logical identifier for the incremental source, "
                "e.g. 'employee_incremental' or 'case_incremental'."
            ),
        ),
        sa.Column(
            'watermark_ts',
            sa.DateTime(timezone=True),
            nullable=False,
            comment=(
                "Timestamp component of the composite high-water mark. "
                "Records with updated_at strictly greater than this value "
                "are selected in the next incremental run."
            ),
        ),
        sa.Column(
            'watermark_id',
            sa.String(length=36),
            nullable=False,
            server_default='',
            comment=(
                "Entity-id component of the composite high-water mark. "
                "Breaks ties when multiple records share the same watermark_ts."
            ),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment="UTC timestamp of the last successful watermark commit.",
        ),
        sa.PrimaryKeyConstraint('pipeline_key'),
    )


def downgrade() -> None:
    """Drop the pipeline_watermarks table."""
    op.drop_table('pipeline_watermarks')
