from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse,TaskResponseList
from app.schemas.response import APIResponse,api_response
from app.services import task_service
from app.models.task import TaskStatus, TaskPriority
from typing import Optional,Literal
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@router.post("",
    response_model=APIResponse,
    status_code=201,
    summary="Tạo task mới",
    description="Thành viên dự án (owner/member) có quyền tạo. Task mới luôn bắt đầu ở trạng thái TODO. Nếu gán assignee, người đó phải là thành viên của dự án.",)
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

@router.get("",
    response_model=APIResponse,
    status_code=200,
    summary="Danh sách task (có filter, search, phân trang)",
    description=(
        "Chỉ trả task thuộc đúng dự án này. Hỗ trợ: search theo title; "
        "filter theo status (TODO/IN_PROGRESS/DONE), priority (LOW/MEDIUM/HIGH), assignee_id; "
        "sort theo created_at hoặc due_date; phân trang theo page/size."
    ),)
def get_tasks(
    project_id: int,
    request: Request,
    search: Optional[str] = None,
    status_task: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[int] = None,
    sort_by: Literal["created_at", "due_date"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = task_service.get_tasks(
        db, project_id, current_user.id,
        search=search, status=status_task, priority=priority, assignee_id=assignee_id,
        sort_by=sort_by, sort_order=sort_order, page=page, size=size,
    )

    item_count = len(result["items"])
    message = f"Lấy danh sách task thành công (trang {result['page']}/{result['total_pages']}, hiển thị {item_count}/{result['total']} task)"

    return api_response(
        status.HTTP_200_OK,
        message,
        {
            "items": [TaskResponseList.model_validate(t) for t in result["items"]],
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "total_pages": result["total_pages"],
        },
        request,
    )