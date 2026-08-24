from fastapi import FastAPI
from app.db.database import Base,engine
from app.models import user,task,project_member,project
from app.core.error_handlers import register_error_handlers
from app.core.exceptions import NotFoundException
from app.routers import auth,users,projects

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
Base.metadata.create_all(bind=engine)

register_error_handlers(app)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Server đang hoạt động bình thường"
    }

@app.get("/test-error")
def test_error():
    raise NotFoundException(detail="Test lỗi 404")