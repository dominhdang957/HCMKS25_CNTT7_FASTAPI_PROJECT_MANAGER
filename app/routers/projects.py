from fastapi import APIRouter, Depends, Request,status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.dependencies import get_current_user 
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse,ProjectUpdate
from app.schemas.response import api_response,APIResponse
from app.services import project_service
from typing import Optional
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberResponse
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post( "",
    response_model=APIResponse,
    status_code=201,
    summary="Tạo dự án mới",
    description="Tạo project mới, người tạo tự động trở thành OWNER (được thêm vào project_members với role OWNER).",)
def create_project(
    project_data: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project = project_service.create_project(
        db, project_data, owner_id=current_user.id
    )
    return api_response(status.HTTP_201_CREATED,"Tạo dự án thành công",ProjectResponse.model_validate(new_project),request)

@router.get("",
    response_model=APIResponse,
    status_code=200,
    summary="Danh sách dự án của tôi",
    description="Trả về các project mà user hiện tại là owner hoặc member. Hỗ trợ tìm theo tên (search).",)
def list_projects(
    request: Request,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = project_service.get_projects_for_user(db, current_user.id, search=search)
    return api_response(
        status.HTTP_200_OK,
        f"Lấy danh sách dự án thành công ({len(projects)} kết quả)",
        [ProjectResponse.model_validate(p) for p in projects],
        request,
    )

@router.get("/{project_id}",
    response_model=APIResponse,
    status_code=200,
    summary="Chi tiết dự án",
    description="Chỉ thành viên (owner hoặc member) của dự án mới xem được. Trả 404 nếu không tồn tại, 403 nếu không phải thành viên.",
)
def get_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.get_project_detail(db, project_id, current_user.id)
    return api_response(
        status.HTTP_200_OK,
        "Lấy chi tiết dự án thành công",
        ProjectResponse.model_validate(project),
        request,
    )


@router.patch("/{project_id}",
    response_model=APIResponse,
    status_code=200,
    summary="Cập nhật dự án",
    description="Chỉ OWNER được cập nhật. Hỗ trợ cập nhật một phần (chỉ gửi field muốn đổi).",)
def update_project(
    project_id: int,
    update_data: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = project_service.update_project(db, project_id, current_user.id, update_data)
    return api_response(
        status.HTTP_200_OK,
        "Cập nhật dự án thành công",
        ProjectResponse.model_validate(project),
        request,
    )


@router.delete("/{project_id}",
    response_model=APIResponse,
    status_code=200,
    summary="Xóa dự án",
    description="Chỉ OWNER được xóa. Xóa luôn toàn bộ project_members liên quan.",)
def delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service.delete_project(db, project_id, current_user.id)
    return api_response(
        status.HTTP_200_OK,
        "Xóa dự án thành công",
        None,
        request,
    )

@router.post("/{project_id}/members",
    response_model=APIResponse,
    status_code=201,
    summary="Thêm thành viên",
    description="Chỉ OWNER được thêm. Không cho gán role OWNER qua API này, không cho thêm trùng user đã là thành viên.",)
def add_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_member = project_service.add_member(db, project_id, current_user.id, member_data)
    return api_response(
        status.HTTP_201_CREATED,
        "Thêm thành viên thành công",
        ProjectMemberResponse.model_validate(new_member),
        request,
    )

@router.delete("/{project_id}/members/{user_id}",
    response_model=APIResponse,
    status_code=200,
    summary="Xóa thành viên",
    description="Chỉ OWNER được xóa. Không thể xóa chính OWNER khỏi dự án.",)
def remove_member(
    project_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service.remove_member(db, project_id, current_user.id, user_id)
    return api_response(
        status.HTTP_200_OK,
        "Xóa thành viên thành công",
        None,
        request,
    )

@router.get("/{project_id}/members",
    response_model=APIResponse,
    status_code=200,
    summary="Danh sách thành viên",
    description="Trả danh sách thành viên kèm role (OWNER/MEMBER). Owner hoặc member đều xem được.",)
def get_members(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    members = project_service.get_members(db, project_id, current_user.id)
    return api_response(
        status.HTTP_200_OK,
        f"Lấy danh sách thành viên thành công ({len(members)} thành viên)",
        [ProjectMemberResponse.model_validate(m) for m in members],
        request,
    )


@router.get("/{project_id}/logs",
    response_model=APIResponse,
    status_code=200,
    summary="Lịch sử hoạt động (Activity log)",
    description="Ghi nhận các thao tác quan trọng: tạo/sửa dự án, thêm/xóa thành viên. Sắp xếp mới nhất lên đầu.",)
def get_logs(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service.check_is_member(db, project_id, current_user.id) 

    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )
    return api_response(
        status.HTTP_200_OK,
        f"Lấy lịch sử hoạt động thành công ({len(logs)} bản ghi)",
        [ActivityLogResponse.model_validate(log) for log in logs],
        request,
    )