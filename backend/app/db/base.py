# This file is used to ensure all SQLAlchemy models are imported before
# initializing the database, so that they are registered properly on the metadata.

from .base_class import Base
from ..models.user import User