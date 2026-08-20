from fastapi import FastAPI
from app.db.database import Base,engine
from app.models import user,task,project_member,project

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def get_root():
    return {"message":"Kết nối thành công server"}



