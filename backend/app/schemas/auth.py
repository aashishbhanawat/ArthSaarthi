from pydantic import BaseModel


class Status(BaseModel):
    setup_needed: bool