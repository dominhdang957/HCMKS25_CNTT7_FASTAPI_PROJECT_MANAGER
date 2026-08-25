from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project
from app.models.project_member import ProjectMember,ProjectMemberRole
from app.schemas.task import TaskCreate,TaskUpdate
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.services.project_service import check_is_member,check_is_owner
from typing import Optional,Literal
from sqlalchemy import asc,desc



def create_task(db: Session, project_id: int, user_id: int, task_data: TaskCreate) -> Task:
    # Bước 1: kiểm tra project tồn tại + user là thành viên (owner hoặc member)
    check_is_member(db, project_id, user_id)

    # Bước 2: nếu có assignee_id, kiểm tra assignee phải là thành viên CỦA project này
    if task_data.assignee_id is not None:
        is_assignee_member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == task_data.assignee_id,
            )
            .first()
        )
        if not is_assignee_member:
            raise BadRequestException(detail="Người được giao việc phải là thành viên của dự án")

    # Bước 3: tạo task
    new_task = Task(
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        assignee_id=task_data.assignee_id,
        priority=task_data.priority,
        due_date=task_data.due_date,
        status=TaskStatus.TODO,  # task mới luôn bắt đầu ở trạng thái TODO
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def get_tasks(
    db: Session,
    project_id: int,
    user_id: int,
    search: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[int] = None,
    sort_by: Literal["created_at", "due_date"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    size: int = 10,
) -> dict:
    check_is_member(db, project_id, user_id)

    query = db.query(Task).filter(Task.project_id == project_id)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)

    # ---- Đếm tổng số kết quả TRƯỚC khi phân trang ----
    total = query.count()

    # ---- Sort ----
    sort_column = getattr(Task, sort_by)
    order_func = desc if sort_order == "desc" else asc
    query = query.order_by(order_func(sort_column))

    # ---- Pagination ----
    offset = (page - 1) * size
    tasks = query.offset(offset).limit(size).all()

    return {
        "items": tasks,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,  # làm tròn lên
    }

def get_task_detail(db: Session, task_id: int, user_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException(detail="Không tìm thấy task")

    # Kiểm tra user có phải thành viên của project chứa task này không
    check_is_member(db, task.project_id, user_id)

    return task


def update_task(db: Session, task_id: int, user_id: int, update_data: TaskUpdate) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException(detail="Không tìm thấy task")

    role = get_project_role(db, task.project_id, user_id)
    if role is None:
        raise ForbiddenException(detail="Bạn không phải thành viên của dự án này")

    is_owner = (role == ProjectMemberRole.OWNER)
    is_assignee = (task.assignee_id == user_id)

    update_fields = update_data.model_dump(exclude_unset=True)

    # ---- Chặn MEMBER thường (không phải owner, không phải assignee) ----
    if not is_owner and not is_assignee:
        raise ForbiddenException(detail="Bạn không có quyền cập nhật task này")

    # ---- Assignee CHỈ được đổi status, không được đổi field khác ----
    if not is_owner and is_assignee:
        allowed_fields = {"status"}
        not_allowed = set(update_fields.keys()) - allowed_fields
        if not_allowed:
            raise ForbiddenException(
                detail=f"Bạn chỉ có quyền cập nhật trạng thái task, không được sửa: {', '.join(not_allowed)}"
            )

    # ---- Validate status transition (đã có từ task 7) ----
    if "status" in update_fields:
        validate_status_transition(task.status, update_fields["status"])

    # ---- Validate assignee mới phải là thành viên project (đã có từ task 4) ----
    if "assignee_id" in update_fields and update_fields["assignee_id"] is not None:
        is_assignee_member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == task.project_id,
                ProjectMember.user_id == update_fields["assignee_id"],
            )
            .first()
        )
        if not is_assignee_member:
            raise BadRequestException(detail="Người được giao việc phải là thành viên của dự án")

    for field, value in update_fields.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, user_id: int) -> None:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException(detail="Không tìm thấy task")

    project = check_is_owner(db, task.project_id, user_id)  # dùng lại hàm đã có sẵn từ phần Project

    db.delete(task)
    db.commit()

VALID_STATUS_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.DONE, TaskStatus.TODO],  # cho phép lùi lại TODO nếu cần
    TaskStatus.DONE: [TaskStatus.IN_PROGRESS],  # cho phép mở lại nếu chưa thực sự xong
}


def validate_status_transition(current_status: TaskStatus, new_status: TaskStatus):
    if current_status == new_status:
        return  # không đổi gì, không cần kiểm tra

    allowed_next = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        raise BadRequestException(
            detail=f"Không thể chuyển task từ '{current_status.value}' sang '{new_status.value}'"
        )

def get_project_role(db: Session, project_id: int, user_id: int) -> Optional[ProjectMemberRole]:
    """Lấy role của user trong project (None nếu không phải thành viên)"""
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    return member.role if member else None