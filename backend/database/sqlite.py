from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import shutil
from typing import Any, List, Optional, Type, TypeVar
from backend.core.config import config_manager
from backend.core.logger import app_logger

Base = declarative_base()
T = TypeVar("T", bound=Base)

class SQLiteManager:
    """
    Manages SQLite connections, migrations, and backups.
    """
    def __init__(self, db_url: str = None):
        self.db_url = db_url or config_manager.get_config().database_url
        connect_args = {"check_same_thread": False} if "sqlite" in self.db_url else {}
        
        self.engine = create_engine(
            self.db_url,
            connect_args=connect_args,
            poolclass=StaticPool,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def initialize_database(self):
        """Creates all tables defined in Base."""
        app_logger.info("Initializing SQLite database schemas...")
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Dependency for getting DB session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def backup(self, backup_path: str):
        """Creates a backup of the sqlite file."""
        if "sqlite:///" in self.db_url:
            db_path = self.db_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                app_logger.info(f"Database backed up to {backup_path}")
            else:
                app_logger.warning("Database file not found for backup.")

    def restore(self, backup_path: str):
        """Restores the database from a backup file."""
        if "sqlite:///" in self.db_url:
            db_path = self.db_url.replace("sqlite:///", "")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, db_path)
                app_logger.info(f"Database restored from {backup_path}")
            else:
                app_logger.error("Backup file not found.")

class BaseRepository:
    """
    Generic Repository Pattern implementation.
    """
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get(self, id: Any) -> Optional[T]:
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Any) -> T:
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        db_obj = self.model(**obj_data)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def update(self, db_obj: T, obj_in: Any) -> T:
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        for field in obj_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_data[field])
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> bool:
        obj = self.get(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False

db_manager = SQLiteManager()
