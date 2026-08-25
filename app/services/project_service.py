from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.schemas.project import ProjectCreate
from typing import Optional
from app.core.exceptions import NotFoundException, ForbiddenException
from app.schemas.project import ProjectUpdate
from app.models.user import User as UserModel
from app.schemas.project_member import ProjectMemberCreate
from app.core.exceptions import BadRequestException
from app.services.activity_log_service import log_activity


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

    log_activity(
        db, new_project.id, owner_id,
        action="CREATE_PROJECT",
        description=f"Tạo dự án '{new_project.name}'",
    )

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
    return check_is_member(db, project_id, user_id)


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

    log_activity(
        db, project_id, user_id,
        action="UPDATE_PROJECT",
        description=f"Cập nhật dự án: {list(update_fields.keys())}",
    )
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    project = check_is_owner(db, project_id, user_id)

    # Xóa các project_members trước (nếu DB chưa cấu hình CASCADE)
    db.query(ProjectMember).filter(ProjectMember.project_id == project_id).delete()

    db.delete(project)
    db.commit()


def add_member(
    db: Session,
    project_id: int,
    owner_id: int,
    member_data: ProjectMemberCreate,
) -> ProjectMember:
    # Bước 1: kiểm tra project tồn tại + người gọi là OWNER
    check_is_owner(db, project_id, owner_id)


    # Bước 3: kiểm tra user muốn thêm có tồn tại không
    target_user = db.query(UserModel).filter(UserModel.id == member_data.user_id).first()
    if not target_user:
        raise NotFoundException(detail="Không tìm thấy user muốn thêm")

    # Bước 4: kiểm tra đã là thành viên chưa (tránh trùng)
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_data.user_id,
        )
        .first()
    )
    if existing:
        raise BadRequestException(detail="User này đã là thành viên của dự án")

    # Bước 5: thêm mới, LUÔN ép role = MEMBER (bỏ qua giá trị client gửi, cho chắc chắn)
    new_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=ProjectMemberRole.MEMBER,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    log_activity(
        db, project_id, owner_id,
        action="ADD_MEMBER",
        description=f"Thêm user id={member_data.user_id} vào dự án",
    )
    return new_member


def remove_member(
    db: Session,
    project_id: int,
    owner_id: int,
    target_user_id: int,
) -> None:
    # Bước 1: kiểm tra project tồn tại + người gọi là OWNER
    check_is_owner(db, project_id, owner_id)

    # Bước 2: tìm dòng project_member cần xóa
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id,
        )
        .first()
    )
    if not member:
        raise NotFoundException(detail="User này không phải thành viên của dự án")

    # Bước 3: không cho xóa chính OWNER (kể cả owner tự xóa chính mình)
    if member.role == ProjectMemberRole.OWNER:
        raise BadRequestException(detail="Không thể xóa chủ dự án (OWNER) khỏi dự án")

    # Bước 4: xóa
    db.delete(member)
    db.commit()

    log_activity(
        db, project_id, owner_id,
        action="REMOVE_MEMBER",
        description=f"Xóa user id={target_user_id} khỏi dự án",
    )


def get_members(db: Session, project_id: int, user_id: int) -> list[ProjectMember]:
    check_is_member(db, project_id, user_id)
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )

def check_is_member(db: Session, project_id: int, user_id: int) -> Project:
    """Kiểm tra project tồn tại + user là thành viên (owner hoặc member), trả về project"""
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