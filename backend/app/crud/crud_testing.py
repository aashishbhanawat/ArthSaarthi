import logging
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine

class TestingCRUD:
    def reset_database(self, db: Session) -> None:
        """
        Drops all tables and recreates them for a clean test environment.
        """
        Base.metadata.drop_all(bind=db.get_bind())
        Base.metadata.create_all(bind=db.get_bind())


    def seed_database(self, db: Session) -> None:
        """
        Seeds the database with any initial data required for tests.
        This is intentionally left empty for E2E tests, as they should
        test the initial setup flow via the UI.
        """
        pass


testing = TestingCRUD()
