import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UsageEvent(Base):
    """
    One billable AI action performed by a user. Used to enforce per-user daily
    quotas (defense-in-depth on top of IP rate limiting) so a single account
    can't burn through the Anthropic / Google spend caps.
    """

    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # search, upload, upload_multiple, recommend
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_usage_user_action_time", "user_id", "action", "created_at"),
    )

    def __repr__(self):
        return f"<UsageEvent user_id={self.user_id} action={self.action}>"
