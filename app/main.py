from fastapi import FastAPI
from app.db.database import Base,engine
import app.models.project
import app.models.project_member
import app.models.task
import app.models.user

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def get_root():
    return {"message":"Kết nối thành công server"}



