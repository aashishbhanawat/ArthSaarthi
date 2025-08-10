import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class AssetAlias(Base):
    __tablename__ = "asset_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    alias_symbol = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False) # e.g., "Zerodha Tradebook", "ICICI Direct"

    asset = relationship("Asset", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint('alias_symbol', 'source', name='_alias_symbol_source_uc'),
    )
