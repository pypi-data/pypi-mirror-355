# ml_observability/events/schemas.py
"""
Event schemas for ML Observability.

This module defines the core event types used for ML observability.
"""
from enum import Enum

class EventType(str, Enum):
    """Event types for observability."""
    TRACE_START = "trace_start"
    TRACE_END = "trace_end"
    SPAN_START = "span_start"
    SPAN_END = "span_end"

class SpanType(str, Enum):
    """Types of spans in a trace."""
    STEP = "STEP"  # A general processing step
    TOOL = "TOOL"  # A tool or external service call
    AGENT = "AGENT"  # An agent action or decision