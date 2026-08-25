from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse
from app.schemas.response import APIResponse,api_response
from app.services import task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@router.post("", response_model=APIResponse)
def create_task(
    project_id: int,
    task_data: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_task = task_service.create_task(db, project_id, current_user.id, task_data)
    return api_response(
        status.HTTP_201_CREATED,
        "Tạo task thành công",
        TaskResponse.model_validate(new_task),
        request,
    )