from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.task import TaskCreate,TaskUpdate
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

def get_tasks(db: Session, project_id: int, user_id: int) -> list[Task]:
    # Chỉ cần là thành viên (owner hoặc member) mới được xem danh sách task
    check_is_member(db, project_id, user_id)

    return (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
        .all()
    )

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

    # Tạm thời: mọi thành viên project đều được sửa task (sẽ siết chặt hơn ở task "Permission matrix")
    check_is_member(db, task.project_id, user_id)

    update_fields = update_data.model_dump(exclude_unset=True)

    # Nếu có đổi assignee_id, kiểm tra assignee mới phải là thành viên project
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