# ml_observability/events/__init__.py
"""Event-driven ML observability components with simplified API."""

from .schemas import (
    EventType, SpanType
)
from .llm_observer import create_llm_observer

__all__ = [
    # Event schemas
    'EventType', 'SpanType',
    
    # LLM Observer
    'create_llm_observer'
]