import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import decrypt_credential, encrypt_credential
from app.crud.base import CRUDBase
from app.models.broker_credential import BrokerCredential
from app.schemas.broker import BrokerCredentialSave


class CRUDBrokerCredential(CRUDBase[BrokerCredential, BrokerCredentialSave, BrokerCredentialSave]):
    def get_by_user_and_provider(
        self, db: Session, user_id: uuid.UUID, provider_name: str
    ) -> Optional[BrokerCredential]:
        return (
            db.query(BrokerCredential)
            .filter(
                BrokerCredential.user_id == user_id,
                BrokerCredential.provider_name == provider_name,
            )
            .first()
        )

    def get_all_by_user(
        self, db: Session, user_id: uuid.UUID
    ) -> List[BrokerCredential]:
        return (
            db.query(BrokerCredential)
            .filter(BrokerCredential.user_id == user_id)
            .all()
        )

    def save_credentials(
        self, db: Session, user_id: uuid.UUID, provider_name: str, api_key: str, api_secret: str
    ) -> BrokerCredential:
        existing = self.get_by_user_and_provider(db, user_id, provider_name)
        encrypted_secret = encrypt_credential(api_secret)

        if existing:
            existing.api_key = api_key
            existing.encrypted_api_secret = encrypted_secret
            existing.is_active = True
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        db_obj = BrokerCredential(
            user_id=user_id,
            provider_name=provider_name,
            api_key=api_key,
            encrypted_api_secret=encrypted_secret,
            is_active=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_session_token(
        self,
        db: Session,
        db_obj: BrokerCredential,
        access_token: str,
        token_issued_at: Optional[datetime] = None,
        token_expires_at: Optional[datetime] = None,
    ) -> BrokerCredential:
        db_obj.encrypted_access_token = encrypt_credential(access_token)
        db_obj.token_issued_at = token_issued_at or datetime.now(timezone.utc)
        db_obj.token_expires_at = token_expires_at
        db_obj.is_active = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_credentials(
        self, db: Session, user_id: uuid.UUID, provider_name: str
    ) -> bool:
        existing = self.get_by_user_and_provider(db, user_id, provider_name)
        if not existing:
            return False
        db.delete(existing)
        db.commit()
        return True

    def get_decrypted_secret(self, db_obj: BrokerCredential) -> str:
        if not db_obj or not db_obj.encrypted_api_secret:
            return ""
        return decrypt_credential(db_obj.encrypted_api_secret)

    def get_decrypted_token(self, db_obj: BrokerCredential) -> str:
        if not db_obj or not db_obj.encrypted_access_token:
            return ""
        return decrypt_credential(db_obj.encrypted_access_token)


crud_broker = CRUDBrokerCredential(BrokerCredential)
