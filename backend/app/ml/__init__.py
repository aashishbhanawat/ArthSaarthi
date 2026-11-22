"""
ArthSaarthi Machine Learning & Edge NLP Subsystem
Provides modular entity extraction, deduplication, financial sentiment analysis,
and on-demand edge model management.
"""

from app.ml.deduplicator import HeadlineDeduplicator
from app.ml.entity_matcher import FastEntityMatcher
from app.ml.model_manager import model_manager
from app.ml.sentiment_engine import SentimentResult, sentiment_engine

__all__ = [
    "FastEntityMatcher",
    "HeadlineDeduplicator",
    "sentiment_engine",
    "SentimentResult",
    "model_manager",
]
