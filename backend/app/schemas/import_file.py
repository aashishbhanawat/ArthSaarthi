
from pydantic import BaseModel


class ImportFile(BaseModel):
    file_name: str
    file_content: str  # Base64 encoded content or direct string content
    file_type: str  # e.g., 'csv', 'xlsx'
