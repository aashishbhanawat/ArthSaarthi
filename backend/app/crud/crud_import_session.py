from app.crud.base import CRUDBase
from app.models.import_session import ImportSession
from app.schemas.import_session import ImportSessionCreate, ImportSessionUpdate


class CRUDImportSession(
    CRUDBase[ImportSession, ImportSessionCreate, ImportSessionUpdate]
):
    # Add any specific methods for import sessions here in the future
    pass


import_session = CRUDImportSession(ImportSession)
