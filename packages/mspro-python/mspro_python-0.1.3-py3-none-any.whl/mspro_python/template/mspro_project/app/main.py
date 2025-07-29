# app/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.utils.database import create_db_and_tables
from app.routes import user

app = FastAPI()
scheduler = AsyncIOScheduler()

# 配置 CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8001",
    # 其他允许的前端地址
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(user.router, prefix="/api")

# 添加分页支持
add_pagination(app)


# 创建所有表
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


# 运行应用
if __name__ == "__main__":
    on_startup()
    # database about
    # alembic revision --autogenerate -m "Add definition field to Function"
    # alembic upgrade head
