import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import decrypt_credential, encrypt_credential
from app.crud.base import CRUDBase
from app.models.broker_credential import BrokerCredential
from app.schemas.broker import BrokerCredentialSave


class CRUDBrokerCredential(
    CRUDBase[BrokerCredential, BrokerCredentialSave, BrokerCredentialSave]
):
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
            db.query(BrokerCredential).filter(BrokerCredential.user_id == user_id).all()
        )

    def save_credentials(
        self,
        db: Session,
        user_id: uuid.UUID,
        provider_name: str,
        api_key: str,
        api_secret: str,
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

    def get_active_provider_instance(
        self, db: Session, user_id: uuid.UUID
    ) -> Optional[object]:
        """Returns an initialized provider instance (ZerodhaKiteProvider or IciciBreezeProvider) if active session exists."""
        creds = self.get_all_by_user(db, user_id=user_id)
        now = datetime.now(timezone.utc)
        for c in creds:
            if c.is_active and c.encrypted_access_token:
                if c.token_expires_at is None or c.token_expires_at > now:
                    token = self.get_decrypted_token(c)
                    secret = self.get_decrypted_secret(c)
                    if c.provider_name == "zerodha_kite":
                        from app.services.providers.zerodha_provider import (
                            ZerodhaKiteProvider,
                        )

                        return ZerodhaKiteProvider(
                            api_key=c.api_key,
                            access_token=token,
                            api_secret=secret,
                        )
                    elif c.provider_name == "icici_breeze":
                        from app.services.providers.icici_breeze_provider import (
                            IciciBreezeProvider,
                        )

                        return IciciBreezeProvider(
                            api_key=c.api_key,
                            session_token=token,
                            api_secret=secret,
                        )
        return None


crud_broker = CRUDBrokerCredential(BrokerCredential)
