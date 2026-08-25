from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.task import TaskCreate
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.services.project_service import check_is_member


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