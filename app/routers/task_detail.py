from fastapi import APIRouter, Depends, Request,status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskResponse,TaskUpdate
from app.schemas.response import APIResponse,api_response
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=APIResponse)
def get_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.get_task_detail(db, task_id, current_user.id)
    return api_response(
        status.HTTP_200_OK,
        "Lấy chi tiết task thành công",
        TaskResponse.model_validate(task),
        request,
    )




@router.patch("/{task_id}", response_model=APIResponse)
def update_task(
    task_id: int,
    update_data: TaskUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.update_task(db, task_id, current_user.id, update_data)
    return api_response(
        status.HTTP_200_OK,
        "Cập nhật task thành công",
        TaskResponse.model_validate(task),
        request,
    )

@router.delete("/{task_id}", response_model=APIResponse)
def delete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_task(db, task_id, current_user.id)
    return api_response(
        status.HTTP_200_OK,
        "Xóa task thành công",
        None,
        request,
    )