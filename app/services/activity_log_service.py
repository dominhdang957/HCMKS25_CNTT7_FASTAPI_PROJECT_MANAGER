from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


def log_activity(db: Session, project_id: int, user_id: int, action: str, description: str = None):
    log = ActivityLog(
        project_id=project_id,
        user_id=user_id,
        action=action,
        description=description,
    )
    db.add(log)
    db.commit()