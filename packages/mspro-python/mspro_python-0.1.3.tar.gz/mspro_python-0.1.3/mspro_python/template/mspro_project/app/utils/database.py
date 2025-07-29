from contextlib import asynccontextmanager, contextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os


load_dotenv()

DATABASE_URL = 'mysql+asyncmy://%s:%s@%s:%s/%s' % (
    os.environ.get('DB_USERNAME'),
    os.environ.get('DB_PASSWORD'),
    os.environ.get('DB_HOST'),
    os.environ.get('DB_PORT'),
    os.environ.get('DB_DATABASE')
)
# for alembic
SYNC_DATABASE_URL = 'mysql+pymysql://%s:%s@%s:%s/%s' % (
    os.environ.get('DB_USERNAME'),
    os.environ.get('DB_PASSWORD'),
    os.environ.get('DB_HOST'),
    os.environ.get('DB_PORT'),
    os.environ.get('DB_DATABASE')
)

# 创建同步引擎供 Celery 使用
sync_engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
sync_session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 创建异步引擎
async_engine = create_async_engine(DATABASE_URL,
                                   echo=True,
                                   pool_size=20,  # 根据需要调整
                                   max_overflow=30,  # 根据需要调整
                                   pool_timeout=30,  # 超时时间
                                   )

# 创建异步会话工厂
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


# 异步创建数据库和表
async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# 异步上下文管理器
@asynccontextmanager
async def get_async_session_context() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_session_context() -> Session:
    session = sync_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# 用于依赖注入的会话生成器
async def get_async_session() -> AsyncSession:
    async with get_async_session_context() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
