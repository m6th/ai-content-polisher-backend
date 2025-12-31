from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app import models, auth
from app.database import get_db
from app.plan_config import get_plan_config
from app.utils.team_utils import get_effective_plan, get_user_team
from app.email_service import send_calendar_reminder
import os

router = APIRouter(prefix="/calendar", tags=["calendar"])

# Pydantic models
class ScheduledContentCreate(BaseModel):
    content_request_id: Optional[int] = None
    generated_content_id: Optional[int] = None
    scheduled_date: datetime
    platform: str
    title: Optional[str] = None
    notes: Optional[str] = None

class ScheduledContentUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None

@router.post("/schedule")
def schedule_content(
    data: ScheduledContentCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule content for publishing (Pro/Business only)"""

    # Get effective plan (considering team membership)
    effective_plan = get_effective_plan(current_user, db)

    # Check if user has calendar feature
    plan_config = get_plan_config(effective_plan)
    calendar_enabled = plan_config.get('features', {}).get('content_calendar', False)

    if not calendar_enabled:
        raise HTTPException(
            status_code=403,
            detail="Le calendrier éditorial est réservé aux plans Pro et Business"
        )

    # Validate that at least content_request_id or generated_content_id is provided
    if not data.content_request_id and not data.generated_content_id:
        raise HTTPException(
            status_code=400,
            detail="Au moins un content_request_id ou generated_content_id doit être fourni"
        )

    # Get user's team and build list of allowed user IDs (for team content access)
    team = get_user_team(current_user, db)
    allowed_user_ids = [current_user.id]
    if team:
        team_members = db.query(models.TeamMember).filter(
            models.TeamMember.team_id == team.id,
            models.TeamMember.status == "active"
        ).all()
        allowed_user_ids.extend([member.user_id for member in team_members])

    # If content_request_id is provided, verify ownership (including team content)
    if data.content_request_id:
        content_request = db.query(models.ContentRequest).filter(
            models.ContentRequest.id == data.content_request_id,
            models.ContentRequest.user_id.in_(allowed_user_ids)
        ).first()

        if not content_request:
            raise HTTPException(status_code=404, detail="Content request not found")

    # If generated_content_id is provided, verify ownership (including team content)
    if data.generated_content_id:
        generated_content = db.query(models.GeneratedContent).join(
            models.ContentRequest
        ).filter(
            models.GeneratedContent.id == data.generated_content_id,
            models.ContentRequest.user_id.in_(allowed_user_ids)
        ).first()

        if not generated_content:
            raise HTTPException(status_code=404, detail="Generated content not found")

    # Create scheduled content
    scheduled = models.ScheduledContent(
        user_id=current_user.id,
        content_request_id=data.content_request_id,
        generated_content_id=data.generated_content_id,
        scheduled_date=data.scheduled_date,
        platform=data.platform,
        title=data.title,
        notes=data.notes,
        status="scheduled"
    )

    db.add(scheduled)
    db.commit()
    db.refresh(scheduled)

    return {
        "id": scheduled.id,
        "scheduled_date": scheduled.scheduled_date.isoformat(),
        "platform": scheduled.platform,
        "status": scheduled.status,
        "title": scheduled.title,
        "created_at": scheduled.created_at.isoformat()
    }

@router.get("/view")
def get_calendar_view(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get calendar view of scheduled content (Pro/Business only)"""

    # Get effective plan (considering team membership)
    effective_plan = get_effective_plan(current_user, db)

    # Check if user has calendar feature
    plan_config = get_plan_config(effective_plan)
    calendar_enabled = plan_config.get('features', {}).get('content_calendar', False)

    if not calendar_enabled:
        raise HTTPException(
            status_code=403,
            detail="Le calendrier éditorial est réservé aux plans Pro et Business"
        )

    # Parse dates or use defaults (current month)
    if start_date:
        start = datetime.fromisoformat(start_date)
    else:
        start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if end_date:
        end = datetime.fromisoformat(end_date)
    else:
        # End of current month
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        end = end.replace(hour=23, minute=59, second=59)

    print(f"📅 Calendar view requested:")
    print(f"  Start date param: {start_date}")
    print(f"  End date param: {end_date}")
    print(f"  Parsed start: {start}")
    print(f"  Parsed end: {end}")

    # Query scheduled content
    query = db.query(models.ScheduledContent).filter(
        models.ScheduledContent.user_id == current_user.id,
        models.ScheduledContent.scheduled_date >= start,
        models.ScheduledContent.scheduled_date <= end
    )

    if platform:
        query = query.filter(models.ScheduledContent.platform == platform)

    scheduled_items = query.order_by(models.ScheduledContent.scheduled_date).all()

    print(f"📊 Found {len(scheduled_items)} scheduled items")
    for item in scheduled_items:
        print(f"  - ID {item.id}: {item.scheduled_date} ({item.scheduled_date.date().isoformat()})")

    # Group by date
    calendar_data = {}
    for item in scheduled_items:
        date_key = item.scheduled_date.date().isoformat()

        if date_key not in calendar_data:
            calendar_data[date_key] = []

        # Get content preview if available
        content_preview = None
        if item.generated_content_id:
            gen_content = db.query(models.GeneratedContent).filter(
                models.GeneratedContent.id == item.generated_content_id
            ).first()
            if gen_content:
                content_preview = gen_content.polished_text[:100] + "..." if len(gen_content.polished_text) > 100 else gen_content.polished_text

        calendar_data[date_key].append({
            "id": item.id,
            "time": item.scheduled_date.strftime("%H:%M"),
            "platform": item.platform,
            "status": item.status,
            "title": item.title,
            "notes": item.notes,
            "content_preview": content_preview,
            "content_request_id": item.content_request_id,
            "generated_content_id": item.generated_content_id
        })

    print(f"🔑 Calendar data keys: {list(calendar_data.keys())}")

    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "calendar": calendar_data,
        "total_scheduled": len(scheduled_items)
    }

@router.put("/{schedule_id}")
def update_scheduled_content(
    schedule_id: int,
    data: ScheduledContentUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update scheduled content (Pro/Business only)"""

    # Get effective plan (considering team membership)
    effective_plan = get_effective_plan(current_user, db)

    # Check if user has calendar feature
    plan_config = get_plan_config(effective_plan)
    calendar_enabled = plan_config.get('features', {}).get('content_calendar', False)

    if not calendar_enabled:
        raise HTTPException(
            status_code=403,
            detail="Le calendrier éditorial est réservé aux plans Pro et Business"
        )

    # Get the scheduled content
    scheduled = db.query(models.ScheduledContent).filter(
        models.ScheduledContent.id == schedule_id,
        models.ScheduledContent.user_id == current_user.id
    ).first()

    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled content not found")

    # Update fields
    if data.scheduled_date:
        scheduled.scheduled_date = data.scheduled_date
    if data.platform:
        scheduled.platform = data.platform
    if data.status:
        scheduled.status = data.status
    if data.title is not None:
        scheduled.title = data.title
    if data.notes is not None:
        scheduled.notes = data.notes

    scheduled.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(scheduled)

    return {
        "id": scheduled.id,
        "scheduled_date": scheduled.scheduled_date.isoformat(),
        "platform": scheduled.platform,
        "status": scheduled.status,
        "title": scheduled.title,
        "notes": scheduled.notes,
        "updated_at": scheduled.updated_at.isoformat()
    }

@router.delete("/{schedule_id}")
def delete_scheduled_content(
    schedule_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete scheduled content (Pro/Business only)"""

    # Get effective plan (considering team membership)
    effective_plan = get_effective_plan(current_user, db)

    # Check if user has calendar feature
    plan_config = get_plan_config(effective_plan)
    calendar_enabled = plan_config.get('features', {}).get('content_calendar', False)

    if not calendar_enabled:
        raise HTTPException(
            status_code=403,
            detail="Le calendrier éditorial est réservé aux plans Pro et Business"
        )

    # Get the scheduled content
    scheduled = db.query(models.ScheduledContent).filter(
        models.ScheduledContent.id == schedule_id,
        models.ScheduledContent.user_id == current_user.id
    ).first()

    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled content not found")

    db.delete(scheduled)
    db.commit()

    return {"message": "Scheduled content deleted successfully"}

@router.get("/upcoming")
def get_upcoming_content(
    days: int = 7,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming scheduled content (Pro/Business only)"""

    # Get effective plan (considering team membership)
    effective_plan = get_effective_plan(current_user, db)

    # Check if user has calendar feature
    plan_config = get_plan_config(effective_plan)
    calendar_enabled = plan_config.get('features', {}).get('content_calendar', False)

    if not calendar_enabled:
        raise HTTPException(
            status_code=403,
            detail="Le calendrier éditorial est réservé aux plans Pro et Business"
        )

    # Get content scheduled in the next N days
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    upcoming = db.query(models.ScheduledContent).filter(
        models.ScheduledContent.user_id == current_user.id,
        models.ScheduledContent.scheduled_date >= now,
        models.ScheduledContent.scheduled_date <= end_date,
        models.ScheduledContent.status == "scheduled"
    ).order_by(models.ScheduledContent.scheduled_date).all()

    results = []
    for item in upcoming:
        # Get content preview
        content_preview = None
        if item.generated_content_id:
            gen_content = db.query(models.GeneratedContent).filter(
                models.GeneratedContent.id == item.generated_content_id
            ).first()
            if gen_content:
                content_preview = gen_content.polished_text[:150] + "..." if len(gen_content.polished_text) > 150 else gen_content.polished_text

        results.append({
            "id": item.id,
            "scheduled_date": item.scheduled_date.isoformat(),
            "platform": item.platform,
            "title": item.title,
            "content_preview": content_preview,
            "days_until": (item.scheduled_date.date() - now.date()).days
        })

    return {
        "upcoming": results,
        "total": len(results),
        "period_days": days
    }

@router.post("/send-reminders")
def trigger_reminders(
    x_cron_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour déclencher l'envoi des rappels de calendrier.
    Sécurisé par une clé secrète pour éviter les appels non autorisés.
    À appeler toutes les heures via un cron job externe (cron-job.org, etc.)
    """
    # Vérifier la clé secrète
    CRON_SECRET = os.getenv("CRON_SECRET", "")
    if not CRON_SECRET or x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Non autorisé")

    now = datetime.utcnow()
    reminders_sent = {"24h": 0, "1h": 0}

    print(f"\n{'='*60}")
    print(f"🔔 SEND REMINDERS TRIGGERED AT: {now.isoformat()}")
    print(f"{'='*60}")

    try:
        # Rappels 24h
        reminder_24h_time = now + timedelta(hours=24)
        print(f"\n📅 Checking 24h reminders:")
        print(f"  Looking for content scheduled between:")
        print(f"    {(reminder_24h_time - timedelta(minutes=30)).isoformat()}")
        print(f"    {(reminder_24h_time + timedelta(minutes=30)).isoformat()}")

        scheduled_24h = db.query(models.ScheduledContent).filter(
            models.ScheduledContent.status == "scheduled",
            models.ScheduledContent.reminder_24h_sent == False,
            models.ScheduledContent.scheduled_date >= reminder_24h_time - timedelta(minutes=30),
            models.ScheduledContent.scheduled_date <= reminder_24h_time + timedelta(minutes=30)
        ).all()

        print(f"  Found {len(scheduled_24h)} items for 24h reminders")

        for scheduled in scheduled_24h:
            user = db.query(models.User).filter(models.User.id == scheduled.user_id).first()
            if not user:
                continue

            content_preview = "Votre contenu planifié"
            if scheduled.generated_content_id:
                gen_content = db.query(models.GeneratedContent).filter(
                    models.GeneratedContent.id == scheduled.generated_content_id
                ).first()
                if gen_content:
                    content_preview = gen_content.polished_text

            scheduled_date_str = scheduled.scheduled_date.strftime("%d/%m/%Y à %H:%M")

            success = send_calendar_reminder(
                to_email=user.email,
                user_name=user.name or "utilisateur",
                content_preview=content_preview,
                platform=scheduled.platform,
                scheduled_date=scheduled_date_str,
                time_before="24h"
            )

            if success:
                scheduled.reminder_24h_sent = True
                scheduled.reminder_24h_sent_at = now
                db.commit()
                reminders_sent["24h"] += 1

        # Rappels 1h
        reminder_1h_time = now + timedelta(hours=1)
        print(f"\n⏰ Checking 1h reminders:")
        print(f"  Current UTC time: {now.isoformat()}")
        print(f"  Looking for content scheduled between:")
        print(f"    {(reminder_1h_time - timedelta(minutes=30)).isoformat()}")
        print(f"    {(reminder_1h_time + timedelta(minutes=30)).isoformat()}")

        # FIXED: Changed from ±5 minutes to ±30 minutes window
        scheduled_1h = db.query(models.ScheduledContent).filter(
            models.ScheduledContent.status == "scheduled",
            models.ScheduledContent.reminder_1h_sent == False,
            models.ScheduledContent.scheduled_date >= reminder_1h_time - timedelta(minutes=30),
            models.ScheduledContent.scheduled_date <= reminder_1h_time + timedelta(minutes=30)
        ).all()

        print(f"  Found {len(scheduled_1h)} items for 1h reminders")

        # Log all scheduled items for debugging
        all_scheduled = db.query(models.ScheduledContent).filter(
            models.ScheduledContent.status == "scheduled",
            models.ScheduledContent.reminder_1h_sent == False
        ).all()
        print(f"\n  📋 All pending scheduled content (not sent 1h reminder yet):")
        for s in all_scheduled:
            print(f"    - ID {s.id}: {s.scheduled_date.isoformat()} (platform: {s.platform})")

        for scheduled in scheduled_1h:
            user = db.query(models.User).filter(models.User.id == scheduled.user_id).first()
            if not user:
                continue

            content_preview = "Votre contenu planifié"
            if scheduled.generated_content_id:
                gen_content = db.query(models.GeneratedContent).filter(
                    models.GeneratedContent.id == scheduled.generated_content_id
                ).first()
                if gen_content:
                    content_preview = gen_content.polished_text

            scheduled_date_str = scheduled.scheduled_date.strftime("%d/%m/%Y à %H:%M")

            print(f"\n  📧 Sending 1h reminder to {user.email} for content ID {scheduled.id}")
            success = send_calendar_reminder(
                to_email=user.email,
                user_name=user.name or "utilisateur",
                content_preview=content_preview,
                platform=scheduled.platform,
                scheduled_date=scheduled_date_str,
                time_before="1h"
            )

            if success:
                print(f"    ✅ Reminder sent successfully")
                scheduled.reminder_1h_sent = True
                scheduled.reminder_1h_sent_at = now
                db.commit()
                reminders_sent["1h"] += 1
            else:
                print(f"    ❌ Failed to send reminder")

        print(f"\n✨ Summary:")
        print(f"  24h reminders sent: {reminders_sent['24h']}")
        print(f"  1h reminders sent: {reminders_sent['1h']}")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "reminders_sent": reminders_sent,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{schedule_id}")
def delete_scheduled_content(
    schedule_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scheduled content (Pro/Business only)"""

    # Get effective plan (considering team membership)
    effective_plan = get_effective_plan(current_user, db)

    # Check if user has calendar feature
    plan_config = get_plan_config(effective_plan)
    calendar_enabled = plan_config.get('features', {}).get('content_calendar', False)

    if not calendar_enabled:
        raise HTTPException(
            status_code=403,
            detail="Le calendrier éditorial est réservé aux plans Pro et Business"
        )

    # Find the scheduled content
    scheduled = db.query(models.ScheduledContent).filter(
        models.ScheduledContent.id == schedule_id,
        models.ScheduledContent.user_id == current_user.id
    ).first()

    if not scheduled:
        raise HTTPException(status_code=404, detail="Contenu planifié non trouvé")

    # Delete it
    db.delete(scheduled)
    db.commit()

    return {"success": True, "message": "Contenu planifié supprimé"}
