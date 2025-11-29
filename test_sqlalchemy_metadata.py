from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.schema import CreateTable

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_model'
    id = Column(Integer, primary_key=True)
    metadata = Column(JSON, nullable=True)

try:
    print(CreateTable(TestModel.__table__).compile(compile_kwargs={"literal_binds": True}))
    print("Successfully created table definition with 'metadata' column.")
except Exception as e:
    print(f"Error: {e}")
