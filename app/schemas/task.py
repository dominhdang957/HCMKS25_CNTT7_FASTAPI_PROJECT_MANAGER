from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass  # project_id lấy từ URL path (VD: /projects/{project_id}/tasks)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskResponseList(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority = TaskPriority.MEDIUM
    model_config = ConfigDict(from_attributes=True)

class TaskResponse(TaskBase):
    id: int
    project_id: int
    status: TaskStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)