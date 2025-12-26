from sqlalchemy.orm import Session
from app import models


def get_effective_plan(user: models.User, db: Session) -> str:
    """
    Get effective plan considering team membership

    - If user has active team membership → return team.plan
    - Otherwise → return user.current_plan

    This ensures all team members have access to features of the team's plan.
    """
    if not user.id:
        return user.current_plan

    # Check if user is member of any active team
    membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == user.id,
        models.TeamMember.status == "active"
    ).first()

    if membership:
        team = db.query(models.Team).filter(
            models.Team.id == membership.team_id
        ).first()

        if team:
            print(f"User {user.id} uses plan '{team.plan}' from team {team.id}")
            return team.plan

    return user.current_plan


def get_user_team(user: models.User, db: Session):
    """
    Get user's team if they are an active member
    Returns Team object or None
    """
    if not user.id:
        return None

    membership = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == user.id,
        models.TeamMember.status == "active"
    ).first()

    if membership:
        return db.query(models.Team).filter(
            models.Team.id == membership.team_id
        ).first()

    return None


def get_effective_credits(user: models.User, db: Session) -> int:
    """
    Get effective credits considering team membership

    - If user is member of active team → return team.team_credits
    - Otherwise → return user.credits_remaining

    This ensures team members use shared team credits pool.
    """
    team = get_user_team(user, db)

    if team:
        return team.team_credits

    return user.credits_remaining


def deduct_credits(user: models.User, db: Session, amount: int = 1) -> bool:
    """
    Deduct credits from user or team pool

    Returns True if successful, False if insufficient credits
    """
    team = get_user_team(user, db)

    if team:
        # Use team credits
        if team.team_credits >= amount:
            team.team_credits -= amount
            db.commit()
            return True
        return False
    else:
        # Use personal credits
        if user.credits_remaining >= amount:
            user.credits_remaining -= amount
            db.commit()
            return True
        return False
