from typing import Any, Dict
from pydantic import BaseModel

def model_dump(obj: BaseModel, **kwargs) -> Dict[str, Any]:
    """
    Pydantic v1/v2 compatible model_dump.
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump(**kwargs)
    return obj.dict(**kwargs)

def model_dump_json(obj: BaseModel, **kwargs) -> str:
    """
    Pydantic v1/v2 compatible model_dump_json.
    """
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json(**kwargs)
    return obj.json(**kwargs)

def model_validate(cls: Any, obj: Any, **kwargs) -> Any:
    """
    Pydantic v1/v2 compatible model_validate.
    """
    if hasattr(cls, "model_validate"):
        return cls.model_validate(obj, **kwargs)
    # Pydantic v1: use from_orm if it's an ORM object, otherwise parse_obj
    if hasattr(cls.Config, "orm_mode") and cls.Config.orm_mode:
        return cls.from_orm(obj)
    return cls.parse_obj(obj)

def model_copy(obj: Any, **kwargs) -> Any:
    """
    Pydantic v1/v2 compatible model_copy.
    """
    if hasattr(obj, "model_copy"):
        return obj.model_copy(**kwargs)
    return obj.copy(**kwargs)

def model_validate_json(cls: Any, json_data: str, **kwargs) -> Any:
    """
    Pydantic v1/v2 compatible model_validate_json.
    """
    if hasattr(cls, "model_validate_json"):
        return cls.model_validate_json(json_data, **kwargs)
    return cls.parse_raw(json_data, **kwargs)
