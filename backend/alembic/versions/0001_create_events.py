"""Create normalized events and source provenance tables."""

from alembic import op
import sqlalchemy as sa

revision = '0001_create_events'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=300), nullable=False),
        sa.Column('event_type', sa.String(length=40), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=150), nullable=True),
        sa.Column('region', sa.String(length=150), nullable=True),
        sa.Column('country', sa.String(length=150), nullable=True),
        sa.Column('venue', sa.String(length=300), nullable=True),
        sa.Column('event_format', sa.String(length=30), nullable=False),
        sa.Column('assistance_available', sa.Boolean(), nullable=True),
        sa.Column('assistance_details', sa.Text(), nullable=True),
        sa.Column('assistance_url', sa.String(length=2048), nullable=True),
        sa.Column('official_url', sa.String(length=2048), nullable=False),
        sa.Column('organizer_name', sa.String(length=200), nullable=True),
        sa.Column('organizer_email', sa.String(length=320), nullable=True),
        sa.Column('topics', sa.JSON(), nullable=False),
        sa.Column('review_status', sa.String(length=32), server_default='pending_review', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "review_status IN ('pending_review', 'changes_requested', 'approved', 'rejected', 'expired', 'archived')",
            name='ck_events_review_status',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_events_starts_at', 'events', ['starts_at'])
    op.create_index('ix_events_official_url', 'events', ['official_url'])
    op.create_index('ix_events_review_status', 'events', ['review_status'])

    op.create_table(
        'event_source_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('source_event_id', sa.String(length=300), nullable=True),
        sa.Column('source_url', sa.String(length=2048), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_name', 'source_event_id', name='uq_source_name_event_id'),
    )


def downgrade() -> None:
    op.drop_table('event_source_records')
    op.drop_index('ix_events_review_status', table_name='events')
    op.drop_index('ix_events_official_url', table_name='events')
    op.drop_index('ix_events_starts_at', table_name='events')
    op.drop_table('events')