from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter()


@router.get("/notifications")
async def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(Notification).where(
            Notification.recipient_user_id == current_user.id
        ).order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    )
    notifications = result.scalars().all()
    return {
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "read_at": n.read_at,
                "created_at": n.created_at,
            }
            for n in notifications
        ],
        "page": page,
        "limit": limit,
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif and notif.read_at is None:
        notif.read_at = datetime.now(timezone.utc)
        await db.commit()
    return {"message": "Marked as read."}
