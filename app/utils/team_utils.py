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
