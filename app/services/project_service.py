from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.schemas.project import ProjectCreate
from typing import Optional
from app.core.exceptions import NotFoundException, ForbiddenException
from app.schemas.project import ProjectUpdate


def create_project(db: Session, project_data: ProjectCreate, owner_id: int) -> Project:
    # Bước 1: Tạo project
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Bước 2: Tự động thêm owner vào bảng project_members với role OWNER
    owner_member = ProjectMember(
        project_id=new_project.id,
        user_id=owner_id,
        role=ProjectMemberRole.OWNER,
    )
    db.add(owner_member)
    db.commit()

    return new_project


def get_projects_for_user(
    db: Session,
    user_id: int,
    search: Optional[str] = None,
) -> list[Project]:
    query = (
        db.query(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(ProjectMember.user_id == user_id)
    )

    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    return query.order_by(Project.created_at.desc()).all()

def get_project_detail(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise NotFoundException(detail="Không tìm thấy dự án")

    is_member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    if not is_member:
        raise ForbiddenException(detail="Bạn không phải thành viên của dự án này")

    return project


def check_is_owner(db: Session, project_id: int, user_id: int) -> Project:
    """Dùng chung cho cả update và delete — kiểm tra tồn tại + đúng là OWNER"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundException(detail="Không tìm thấy dự án")

    if project.owner_id != user_id:
        raise ForbiddenException(detail="Chỉ chủ dự án (OWNER) mới có quyền thực hiện thao tác này")

    return project


def update_project(db: Session, project_id: int, user_id: int, update_data: ProjectUpdate) -> Project:
    project = check_is_owner(db, project_id, user_id)

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    project = check_is_owner(db, project_id, user_id)

    # Xóa các project_members trước (nếu DB chưa cấu hình CASCADE)
    db.query(ProjectMember).filter(ProjectMember.project_id == project_id).delete()

    db.delete(project)
    db.commit()