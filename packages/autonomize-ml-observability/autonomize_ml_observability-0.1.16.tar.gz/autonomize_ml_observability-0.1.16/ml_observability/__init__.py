# ml_observability/__init__.py
"""
ML Observability SDK

This module provides tools for monitoring and tracking ML model usage,
with a focus on LLM observability.
"""

import logging
from typing import Dict, Any, Optional

from .simple_sdk import (
    start_trace, end_trace,
    start_span, end_span,
    monitor_llm_call,
    configure_sdk
)

from .events.llm_observer import (
    create_llm_observer,
    LLMObserver
)

from .observability.cost_tracking import (
    CostTracker,
    get_cost_tracker
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = [
    # Core SDK functions
    'start_trace', 'end_trace',
    'start_span', 'end_span',
    'monitor_llm_call',
    'configure_sdk',
    
    # LLM monitoring
    'create_llm_observer',
    'LLMObserver',
    
    # Cost tracking
    'CostTracker',
    'get_cost_tracker'
]