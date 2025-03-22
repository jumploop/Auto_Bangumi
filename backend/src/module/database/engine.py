from sqlmodel import Session, SQLModel, create_engine
from contextlib import asynccontextmanager

from module.conf import DATA_PATH

engine = create_engine(DATA_PATH)

db_session = Session(engine)


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, pool_pre_ping=True)

    @asynccontextmanager
    async def session(self):
        """支持异步上下文管理的会话"""
        from sqlmodel import Session
        with Session(self.engine) as session:
            yield session

    def migrate(self):
        """自动化迁移"""
        SQLModel.metadata.create_all(self.engine)
