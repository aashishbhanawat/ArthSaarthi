from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.ml.model_manager import model_manager
from app.ml.sentiment_engine import sentiment_engine
from app.models.user import User

router = APIRouter()


def get_ml_manager_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Restricts model weight download and deletion to administrators in server mode."""
    if settings.DEPLOYMENT_MODE == "server" and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Shared Edge ML model management is restricted to administrators.",
        )
    return current_user


class EdgeModelResponse(BaseModel):
    id: str
    name: str
    description: str
    size_mb: float
    status: str
    progress_percentage: int
    downloaded_bytes: int
    total_bytes: int
    error_message: str | None = None
    system_dependency: str | None = None
    system_dependency_satisfied: bool | None = None


class SentimentTestRequest(BaseModel):
    text: str


class SentimentTestResponse(BaseModel):
    label: str
    score: float
    engine: str


@router.get("/models", response_model=List[EdgeModelResponse])
def get_edge_models(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Lists available edge ML models and their download status."""
    return model_manager.list_models()


@router.post("/models/{model_id}/download", response_model=EdgeModelResponse)
def download_edge_model(
    model_id: str,
    current_user: User = Depends(get_ml_manager_user),
) -> Any:
    """Starts background download of an edge model."""
    try:
        return model_manager.start_download(model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start download: {e}")


@router.get("/models/{model_id}/progress", response_model=EdgeModelResponse)
def get_model_download_progress(
    model_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Gets real-time progress for a model download."""
    try:
        return model_manager.get_model_status(model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/models/{model_id}")
def delete_edge_model(
    model_id: str,
    current_user: User = Depends(get_ml_manager_user),
) -> Any:
    """Deletes edge model weights from local storage."""
    deleted = model_manager.delete_model(model_id)
    return {"model_id": model_id, "deleted": deleted, "status": "NOT_DOWNLOADED"}


@router.post("/sentiment/test", response_model=SentimentTestResponse)
def test_headline_sentiment(
    payload: SentimentTestRequest,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Evaluates sample text using the active sentiment engine (FinBERT ONNX or Lexicon)."""
    res = sentiment_engine.analyze(payload.text)
    return {
        "label": res.label,
        "score": res.score,
        "engine": res.engine,
    }
