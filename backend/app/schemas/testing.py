from datetime import date
from pydantic import BaseModel


class MockDatePayload(BaseModel):
    mock_date: date
