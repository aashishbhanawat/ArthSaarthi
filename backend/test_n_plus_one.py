import sys
import os
import uuid
import time
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import event

# Add the backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ["SECRET_KEY"] = "dummy"

# We can simply run tests to see if queries are fewer, or write a dedicated sqlalchemy listener count.
from app.db.session import SessionLocal
from app.crud.crud_dashboard import _calculate_dashboard_summary
from app.models.user import User

db = SessionLocal()
try:
    user = db.query(User).first()
    if not user:
        print("No users in db, exiting test script.")
        sys.exit(0)

    # query counter
    query_count = 0
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        global query_count
        query_count += 1

    event.listen(db.get_bind(), "before_cursor_execute", count_queries)

    print("Running dashboard summary calculation...")
    _calculate_dashboard_summary(db=db, user=user)
    print(f"Total queries executed: {query_count}")

finally:
    db.close()
