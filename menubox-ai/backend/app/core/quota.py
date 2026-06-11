"""
Per-user daily quotas for billable AI actions.

Durable (DB-backed) defense-in-depth on top of the IP rate limiting in
app.core.rate_limit — survives Render free-tier cold starts and caps how much
any single account can spend, regardless of IP. The provider-side spend caps
(Anthropic / Google Cloud) remain the ultimate backstop.

Usage:
    current_user: User = Depends(daily_quota("search", 30))
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.usage_event import UsageEvent


def daily_quota(action: str, limit: int):
    """
    Build a dependency that enforces `limit` uses of `action` per user per
    rolling 24h. Records the attempt before the endpoint runs (so failed calls
    still count — conservative, prevents retry-spam) and raises 429 when the
    cap is reached. Returns the authenticated User so it can replace
    get_current_user in the endpoint signature.
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        since = datetime.now(timezone.utc) - timedelta(days=1)
        used = (
            db.query(UsageEvent)
            .filter(
                UsageEvent.user_id == current_user.id,
                UsageEvent.action == action,
                UsageEvent.created_at >= since,
            )
            .count()
        )

        if used >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily limit reached for this action ({limit}/day). Please try again tomorrow.",
            )

        db.add(UsageEvent(user_id=current_user.id, action=action))
        db.commit()
        return current_user

    return dependency
