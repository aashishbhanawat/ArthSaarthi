import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class AssetAlias(Base):
    __tablename__ = "asset_aliases"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id = Column(GUID, ForeignKey("assets.id"), nullable=False)
    alias_symbol = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False) # e.g., "Zerodha Tradebook", "ICICI Direct"

    asset = relationship("Asset", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint('alias_symbol', 'source', name='_alias_symbol_source_uc'),
    )
