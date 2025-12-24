from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import secrets
from app import models, auth
from app.database import get_db
from app.plan_config import get_plan_config

router = APIRouter(prefix="/teams", tags=["teams"])

# Pydantic models
class TeamCreate(BaseModel):
    name: str

class TeamInvite(BaseModel):
    email: EmailStr

class TeamMemberUpdate(BaseModel):
    role: Optional[str] = None

@router.post("/create")
def create_team(
    data: TeamCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a team (Pro/Business only)"""

    # Check if user has multi-user feature
    plan_config = get_plan_config(current_user.current_plan)
    max_members = plan_config.get('features', {}).get('multi_users', 1)

    if max_members <= 1:
        raise HTTPException(
            status_code=403,
            detail="Les équipes sont réservées aux plans Pro et Business"
        )

    # Check if user already owns a team
    existing_team = db.query(models.Team).filter(
        models.Team.owner_id == current_user.id
    ).first()

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail="Vous avez déjà une équipe"
        )

    # Create team
    team = models.Team(
        name=data.name,
        owner_id=current_user.id,
        plan=current_user.current_plan,
        max_members=max_members
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    # Add owner as first member
    member = models.TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="owner",
        status="active"
    )

    db.add(member)
    db.commit()

    return {
        "id": team.id,
        "name": team.name,
        "plan": team.plan,
        "max_members": team.max_members,
        "created_at": team.created_at.isoformat()
    }

@router.get("/my-team")
def get_my_team(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's team information"""

    # Find team where user is a member
    membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == current_user.id,
        models.TeamMember.status == "active"
    ).first()

    if not membership:
        return {"team": None, "membership": None}

    # Get team details
    team = db.query(models.Team).filter(
        models.Team.id == membership.team_id
    ).first()

    if not team:
        return {"team": None, "membership": None}

    # Get all team members
    members = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team.id,
        models.TeamMember.status == "active"
    ).all()

    members_data = []
    for m in members:
        user = db.query(models.User).filter(models.User.id == m.user_id).first()
        if user:
            members_data.append({
                "id": m.id,
                "user_id": m.user_id,
                "email": user.email,
                "name": user.name,
                "role": m.role,
                "joined_at": m.joined_at.isoformat()
            })

    # Get pending invitations
    invitations = db.query(models.TeamInvitation).filter(
        models.TeamInvitation.team_id == team.id,
        models.TeamInvitation.status == "pending",
        models.TeamInvitation.expires_at > datetime.utcnow()
    ).all()

    invitations_data = [{
        "id": inv.id,
        "email": inv.email,
        "created_at": inv.created_at.isoformat(),
        "expires_at": inv.expires_at.isoformat()
    } for inv in invitations]

    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "plan": team.plan,
            "max_members": team.max_members,
            "current_members": len(members_data),
            "created_at": team.created_at.isoformat()
        },
        "membership": {
            "role": membership.role,
            "joined_at": membership.joined_at.isoformat()
        },
        "members": members_data,
        "pending_invitations": invitations_data
    }

@router.post("/invite")
def invite_member(
    data: TeamInvite,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a member to the team (owner/admin only)"""

    # Get user's team
    membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == current_user.id,
        models.TeamMember.status == "active"
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Vous n'appartenez à aucune équipe")

    # Check if user has permission to invite
    if membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Seuls les propriétaires et administrateurs peuvent inviter des membres"
        )

    # Get team
    team = db.query(models.Team).filter(models.Team.id == membership.team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Équipe introuvable")

    # Check if team is full
    current_members = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team.id,
        models.TeamMember.status == "active"
    ).count()

    if current_members >= team.max_members:
        raise HTTPException(
            status_code=400,
            detail=f"L'équipe est complète ({team.max_members} membres max)"
        )

    # Check if user is already invited or member
    existing_member = db.query(models.TeamMember).join(
        models.User
    ).filter(
        models.TeamMember.team_id == team.id,
        models.User.email == data.email
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="Cet utilisateur est déjà membre de l'équipe")

    existing_invitation = db.query(models.TeamInvitation).filter(
        models.TeamInvitation.team_id == team.id,
        models.TeamInvitation.email == data.email,
        models.TeamInvitation.status == "pending",
        models.TeamInvitation.expires_at > datetime.utcnow()
    ).first()

    if existing_invitation:
        raise HTTPException(status_code=400, detail="Une invitation est déjà en attente pour cet email")

    # Create invitation
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    invitation = models.TeamInvitation(
        team_id=team.id,
        email=data.email,
        invited_by=current_user.id,
        token=token,
        status="pending",
        expires_at=expires_at
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # TODO: Send invitation email with token

    return {
        "id": invitation.id,
        "email": invitation.email,
        "token": token,
        "expires_at": invitation.expires_at.isoformat(),
        "invitation_url": f"/teams/accept-invitation?token={token}"
    }

@router.post("/accept-invitation")
def accept_invitation(
    token: str = Query(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a team invitation"""

    # Find invitation
    invitation = db.query(models.TeamInvitation).filter(
        models.TeamInvitation.token == token,
        models.TeamInvitation.status == "pending"
    ).first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation introuvable")

    # Check if expired
    if invitation.expires_at < datetime.utcnow():
        invitation.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Cette invitation a expiré")

    # Check if email matches
    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="Cette invitation est destinée à un autre email"
        )

    # Check if user is already in a team
    existing_membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == current_user.id,
        models.TeamMember.status == "active"
    ).first()

    if existing_membership:
        raise HTTPException(
            status_code=400,
            detail="Vous êtes déjà membre d'une équipe"
        )

    # Get team
    team = db.query(models.Team).filter(models.Team.id == invitation.team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Équipe introuvable")

    # Check if team is full
    current_members = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team.id,
        models.TeamMember.status == "active"
    ).count()

    if current_members >= team.max_members:
        raise HTTPException(
            status_code=400,
            detail="L'équipe est complète"
        )

    # Add user to team
    member = models.TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="member",
        status="active"
    )

    db.add(member)

    # Mark invitation as accepted
    invitation.status = "accepted"

    db.commit()

    return {
        "message": "Vous avez rejoint l'équipe avec succès",
        "team": {
            "id": team.id,
            "name": team.name,
            "plan": team.plan
        }
    }

@router.delete("/members/{member_id}")
def remove_member(
    member_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the team (owner/admin only)"""

    # Get user's team
    user_membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == current_user.id,
        models.TeamMember.status == "active"
    ).first()

    if not user_membership:
        raise HTTPException(status_code=404, detail="Vous n'appartenez à aucune équipe")

    # Check permissions
    if user_membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Seuls les propriétaires et administrateurs peuvent retirer des membres"
        )

    # Get member to remove
    member = db.query(models.TeamMember).filter(
        models.TeamMember.id == member_id,
        models.TeamMember.team_id == user_membership.team_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable")

    # Cannot remove owner
    if member.role == "owner":
        raise HTTPException(
            status_code=403,
            detail="Le propriétaire ne peut pas être retiré"
        )

    # Cannot remove yourself unless you're leaving
    if member.user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Utilisez l'endpoint /teams/leave pour quitter l'équipe"
        )

    # Remove member
    member.status = "removed"
    db.commit()

    return {"message": "Membre retiré avec succès"}

@router.post("/leave")
def leave_team(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Leave current team"""

    # Get user's membership
    membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == current_user.id,
        models.TeamMember.status == "active"
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Vous n'appartenez à aucune équipe")

    # Cannot leave if owner (must transfer ownership first)
    if membership.role == "owner":
        raise HTTPException(
            status_code=403,
            detail="Le propriétaire doit transférer la propriété avant de quitter"
        )

    # Remove membership
    membership.status = "removed"
    db.commit()

    return {"message": "Vous avez quitté l'équipe avec succès"}

@router.put("/update")
def update_team(
    name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update team details (owner only)"""

    # Get user's team
    membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == current_user.id,
        models.TeamMember.status == "active"
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Vous n'appartenez à aucune équipe")

    # Check if owner
    if membership.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Seul le propriétaire peut modifier l'équipe"
        )

    # Get team
    team = db.query(models.Team).filter(models.Team.id == membership.team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Équipe introuvable")

    # Update team
    team.name = name
    team.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(team)

    return {
        "id": team.id,
        "name": team.name,
        "updated_at": team.updated_at.isoformat()
    }
