from pydantic import BaseModel


# Properties to receive on item creation
class PortfolioCreate(BaseModel):
    name: str
    description: str | None = None


# Properties to receive on item update
class PortfolioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


# Properties shared by models stored in DB
class PortfolioInDBBase(BaseModel):
    id: int
    name: str
    description: str | None = None
    user_id: int

    class Config:
        from_attributes = True


# Properties to return to client
class Portfolio(PortfolioInDBBase):
    pass


# Properties stored in DB
class PortfolioInDB(PortfolioInDBBase):
    pass