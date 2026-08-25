from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)       # VD: "CREATE_PROJECT", "ADD_MEMBER"
    description = Column(Text, nullable=True)          # VD: "Đã thêm user X vào dự án"
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())