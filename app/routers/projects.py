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

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=APIResponse)
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

@router.get("", response_model=APIResponse)
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

@router.get("/{project_id}", response_model=APIResponse)
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


@router.patch("/{project_id}", response_model=APIResponse)
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


@router.delete("/{project_id}", response_model=APIResponse)
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

@router.post("/{project_id}/members", response_model=APIResponse)
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

@router.delete("/{project_id}/members/{user_id}", response_model=APIResponse)
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

@router.get("/{project_id}/members", response_model=APIResponse)
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