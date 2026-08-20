from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.task import Task, TaskStatus, TaskPriority


def seed_data(db: Session):
    # ---- Kiểm tra tránh seed trùng lặp nếu chạy nhiều lần ----
    if db.query(User).first():
        print(" Dữ liệu đã tồn tại, bỏ qua seed để tránh trùng lặp.")
        return

    # ---- 1. Tạo users ----
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        full_name="Quản trị viên",
        role=UserRole.ADMIN,
        is_active=True,
    )
    user1 = User(
        email="minh@example.com",
        password_hash=hash_password("user123"),
        full_name="Minh Đặng",
        role=UserRole.USER,
        is_active=True,
    )
    user2 = User(
        email="lan@example.com",
        password_hash=hash_password("user123"),
        full_name="Nguyễn Thị Lan",
        role=UserRole.USER,
        is_active=True,
    )
    db.add_all([admin, user1, user2])
    db.commit()
    db.refresh(admin)
    db.refresh(user1)
    db.refresh(user2)
    print(f"Đã tạo {3} users")

    # ---- 2. Tạo projects ----
    project1 = Project(
        name="Website bán hàng",
        description="Dự án xây dựng website thương mại điện tử",
        owner_id=user1.id,
    )
    project2 = Project(
        name="App quản lý kho",
        description="Ứng dụng quản lý kho hàng nội bộ",
        owner_id=user2.id,
    )
    db.add_all([project1, project2])
    db.commit()
    db.refresh(project1)
    db.refresh(project2)
    print(f"Đã tạo {2} projects")

    # ---- 3. Tạo project_members ----
    members = [
        ProjectMember(project_id=project1.id, user_id=user1.id, role=ProjectMemberRole.OWNER),
        ProjectMember(project_id=project1.id, user_id=user2.id, role=ProjectMemberRole.MEMBER),
        ProjectMember(project_id=project2.id, user_id=user2.id, role=ProjectMemberRole.OWNER),
        ProjectMember(project_id=project2.id, user_id=user1.id, role=ProjectMemberRole.MEMBER),
    ]
    db.add_all(members)
    db.commit()
    print(f" Đã tạo {len(members)} project_members")

    # ---- 4. Tạo tasks ----
    now = datetime.now(timezone.utc)
    tasks = [
        Task(
            project_id=project1.id,
            title="Thiết kế giao diện trang chủ",
            description="Làm UI/UX cho trang chủ website",
            assignee_id=user1.id,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=now + timedelta(days=3),
        ),
        Task(
            project_id=project1.id,
            title="Tích hợp thanh toán",
            description="Kết nối cổng thanh toán VNPay",
            assignee_id=user2.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=now + timedelta(days=7),
        ),
        Task(
            project_id=project2.id,
            title="Thiết kế database kho hàng",
            description="Xây dựng schema quản lý tồn kho",
            assignee_id=user2.id,
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
            due_date=now - timedelta(days=1),
        ),
        Task(
            project_id=project2.id,
            title="Viết báo cáo xuất nhập kho",
            description=None,
            assignee_id=None,
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            due_date=None,
        ),
    ]
    db.add_all(tasks)
    db.commit()
    print(f" Đã tạo {len(tasks)} tasks")

    print(" Seed dữ liệu hoàn tất!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()