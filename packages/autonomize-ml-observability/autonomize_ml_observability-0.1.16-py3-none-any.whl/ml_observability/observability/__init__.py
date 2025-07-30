"""
ML Observability core components.

This module provides monitoring and observability capabilities for ML systems,
particularly focusing on LLM applications.
"""

from .monitor import (
    initialize, 
    monitor, 
    identify
)
from .tracing import (
    AgentSpanType, 
    get_tracer,
    trace_agent as agent,
    trace_step as agent_step,
    span,
    end_active_run,
    get_tracking_uri,
    get_experiment_by_name,
    search_runs
)
from .cost_tracking import CostTracker, get_cost_tracker

# Create tool as an alias for trace_step with TOOL type
def tool(name=None, attributes=None):
    """
    Decorator for tool functions.
    Automatically wraps the function execution in a span with type TOOL.
    """
    from .tracing import trace_step, AgentSpanType
    return trace_step(name, AgentSpanType.TOOL, attributes)

__all__ = [
    # Monitoring
    'initialize',
    'monitor',
    'identify',
    
    # Tracing
    'AgentSpanType',
    'get_tracer',
    'agent',
    'agent_step',
    'span',
    'tool',
    'end_active_run',
    'get_tracking_uri',
    'get_experiment_by_name',
    'search_runs',
    
    # Cost Tracking
    'CostTracker',
    'get_cost_tracker'
]