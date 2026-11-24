from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.workout import WorkoutAssignment, WorkoutSession, WorkoutVideo, WorkoutVideoProgress

router = APIRouter()


@router.get("/workouts/today")
async def get_workout_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    assignment_result = await db.execute(
        select(WorkoutAssignment).where(
            WorkoutAssignment.user_id == current_user.id,
            WorkoutAssignment.status == "ACTIVE",
        ).order_by(WorkoutAssignment.start_date.desc())
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        return {"session": None, "message": "No workout assigned."}

    day_num = (today - assignment.start_date).days + 1
    session_result = await db.execute(
        select(WorkoutSession).where(
            WorkoutSession.workout_plan_id == assignment.workout_plan_id,
            WorkoutSession.day_number == day_num,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return {"session": None, "message": "No session for today."}

    # Get videos
    videos_result = await db.execute(
        select(WorkoutVideo).where(WorkoutVideo.workout_session_id == session.id)
        .order_by(WorkoutVideo.display_order)
    )
    videos = videos_result.scalars().all()

    # Get progress
    progress_result = await db.execute(
        select(WorkoutVideoProgress).where(
            WorkoutVideoProgress.assignment_id == assignment.id,
        )
    )
    progress_records = {str(p.video_id): p for p in progress_result.scalars().all()}

    return {
        "assignment_id": str(assignment.id),
        "day_number": day_num,
        "session": {
            "id": str(session.id),
            "title": session.title,
            "videos": [
                {
                    "id": str(v.id),
                    "title": v.title,
                    "duration_seconds": v.duration_seconds,
                    "required": v.required,
                    "min_coverage_pct": float(v.min_coverage_pct),
                    "eligible_for_completion": progress_records.get(str(v.id), {}).eligible_for_completion if str(v.id) in progress_records else False,
                    "completed_at": progress_records[str(v.id)].completed_at if str(v.id) in progress_records else None,
                }
                for v in videos
            ],
        },
    }


@router.post("/workouts/videos/{video_id}/progress")
async def record_video_progress(
    video_id: str,
    assignment_id: str,
    covered_seconds: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update video watch progress."""
    video_result = await db.execute(
        select(WorkoutVideo).where(WorkoutVideo.id == video_id)
    )
    video = video_result.scalar_one_or_none()
    if not video:
        return {"error": "Video not found."}

    progress_result = await db.execute(
        select(WorkoutVideoProgress).where(
            WorkoutVideoProgress.assignment_id == assignment_id,
            WorkoutVideoProgress.video_id == video_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    if not progress:
        progress = WorkoutVideoProgress(
            assignment_id=assignment_id,
            video_id=video_id,
            covered_seconds=0,
            eligible_for_completion=False,
        )
        db.add(progress)

    progress.covered_seconds = max(progress.covered_seconds, covered_seconds)

    if video.duration_seconds > 0:
        coverage_pct = (progress.covered_seconds / video.duration_seconds) * 100
        progress.eligible_for_completion = coverage_pct >= float(video.min_coverage_pct)

    await db.commit()
    return {
        "covered_seconds": progress.covered_seconds,
        "eligible_for_completion": progress.eligible_for_completion,
    }
