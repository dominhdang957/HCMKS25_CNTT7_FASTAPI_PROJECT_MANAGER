from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.project_member import ProjectMemberRole


class ProjectMemberBase(BaseModel):
    user_id: int
    role: ProjectMemberRole


class ProjectMemberCreate(BaseModel):
    user_id: int  # project_id lấy từ URL path (VD: /projects/{project_id}/members)


class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole


class ProjectMemberResponse(ProjectMemberBase):
    project_id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)