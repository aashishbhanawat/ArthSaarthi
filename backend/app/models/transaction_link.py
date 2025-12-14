import uuid

from sqlalchemy import Column, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import GUID


class TransactionLink(Base):
    __tablename__ = "transaction_links"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    sell_transaction_id = Column(GUID, ForeignKey("transactions.id"), nullable=False)
    buy_transaction_id = Column(GUID, ForeignKey("transactions.id"), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)

    sell_transaction = relationship(
        "Transaction",
        foreign_keys=[sell_transaction_id],
        back_populates="sell_links",
    )
    buy_transaction = relationship(
        "Transaction",
        foreign_keys=[buy_transaction_id],
        back_populates="buy_links",
    )
