"""
Simple ML Observability SDK

This module provides a lightweight SDK that sends observability events
to the Genesis Service ModelHub API instead of processing them locally.

The Genesis API handles all the complex event processing, experiment management,
and MLflow integration. This SDK just needs to create events and POST them.

Usage:
    from ml_observability.simple_sdk import start_trace, start_span, end_span, end_trace
    
    # Start a trace
    trace_id = start_trace("my_agent", inputs={"query": "hello"})
    
    # Start spans
    span_id = start_span("llm_call", trace_id=trace_id, inputs={"model": "gpt-4"})
    
    # End spans
    end_span(span_id, outputs={"response": "Hi there!"})
    
    # End trace
    end_trace(trace_id, outputs={"final": "complete"})
"""

import json
import uuid
import time
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Default Genesis API configuration
DEFAULT_API_BASE_URL = "http://localhost:8001"
DEFAULT_API_ENDPOINT = "/modelhub/api/v1/observability/events"

class SimpleMLObservabilitySDK:
    """
    Simple SDK for ML Observability that sends events to Genesis API.
    
    This SDK creates observability events and sends them via HTTP to the
    Genesis Service ModelHub API, which handles all the processing.
    """
    
    def __init__(self, 
                 api_base_url: str = DEFAULT_API_BASE_URL,
                 api_endpoint: str = DEFAULT_API_ENDPOINT,
                 timeout: int = 30):
        """
        Initialize the Simple ML Observability SDK.
        
        Args:
            api_base_url: Base URL of the Genesis API server
            api_endpoint: API endpoint for sending events
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_endpoint = api_endpoint
        self.timeout = timeout
        
        logger.info(f"Initialized Simple ML Observability SDK")
        logger.info(f"API URL: {self.api_base_url}{self.api_endpoint}")
    
    def generate_id(self) -> str:
        """Generate a unique ID for traces and spans."""
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def create_event(self, event_type: str, trace_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create a basic event structure.
        
        Args:
            event_type: Type of event (trace_start, span_start, etc.)
            trace_id: Trace ID
            **kwargs: Additional event data
            
        Returns:
            Event dictionary
        """
        event = {
            "event_id": self.generate_id(),
            "event_type": event_type,
            "timestamp": self.get_timestamp(),
            "trace_id": trace_id,
            **kwargs
        }
        return event
    
    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send a single event to the Genesis API.
        
        Args:
            event: Event to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.api_base_url}{self.api_endpoint}"
            
            logger.debug(f"Sending event to {url}")
            logger.debug(f"Event: {event}")
            
            response = requests.post(
                url,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                
                if success:
                    logger.info(f"✅ Successfully sent event: {event['event_type']}")
                else:
                    logger.error(f"❌ Failed to send event: {result.get('error', 'Unknown error')}")
                
                return success
            else:
                logger.error(f"❌ API call failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending event: {str(e)}")
            return False
    
    def start_trace(self, 
                   name: str,
                   inputs: Dict[str, Any] = None,
                   attributes: Dict[str, Any] = None) -> str:
        """
        Start a new trace.
        
        Args:
            name: Name of the trace
            inputs: Input data for the trace
            attributes: Additional attributes
            
        Returns:
            Generated trace ID
        """
        trace_id = self.generate_id()
        
        event = self.create_event(
            event_type="trace_start",
            trace_id=trace_id,
            name=name,
            run_name=f"trace_{name}_{int(time.time())}",
            inputs=inputs or {},
            attributes=attributes or {},
            outputs=None,
            metrics=None,
            status=None,
            error=None,
            duration_ms=None
        )
        
        success = self.send_event(event)
        if success:
            logger.info(f"🚀 Started trace '{name}' with ID: {trace_id}")
        else:
            logger.error(f"❌ Failed to start trace '{name}'")
            
        return trace_id
    
    def end_trace(self,
                 trace_id: str,
                 outputs: Dict[str, Any] = None,
                 metrics: List[Dict[str, Any]] = None,
                 status: str = "OK",
                 error: str = None) -> bool:
        """
        End a trace.
        
        Args:
            trace_id: Trace ID to end
            outputs: Output data from the trace
            metrics: List of metrics
            status: Status ("OK" or "ERROR")
            error: Error message if status is ERROR
            
        Returns:
            True if successful
        """
        event = self.create_event(
            event_type="trace_end",
            trace_id=trace_id,
            name=None,
            run_name=None,
            attributes=None,
            inputs=None,
            outputs=outputs or {},
            metrics=metrics or [],
            status=status,
            error=error,
            duration_ms=None  # Duration will be calculated by the API
        )
        
        success = self.send_event(event)
        if success:
            logger.info(f"🏁 Ended trace: {trace_id}")
        else:
            logger.error(f"❌ Failed to end trace: {trace_id}")
            
        return success
    
    def start_span(self,
                  name: str,
                  trace_id: str,
                  span_type: str = "STEP",
                  parent_span_id: str = None,
                  inputs: Dict[str, Any] = None,
                  attributes: Dict[str, Any] = None) -> str:
        """
        Start a new span.
        
        Args:
            name: Name of the span
            trace_id: Trace ID this span belongs to
            span_type: Type of span (STEP, TOOL, AGENT, etc.)
            parent_span_id: Parent span ID for nesting
            inputs: Input data for the span
            attributes: Additional attributes
            
        Returns:
            Generated span ID
        """
        span_id = self.generate_id()
        
        event = self.create_event(
            event_type="span_start",
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            span_type=span_type,
            parent_span_id=parent_span_id,
            inputs=inputs or {},
            attributes=attributes or {}
        )
        
        success = self.send_event(event)
        if success:
            logger.info(f"📍 Started span '{name}' with ID: {span_id}")
        else:
            logger.error(f"❌ Failed to start span '{name}'")
            
        return span_id
    
    def end_span(self,
                span_id: str,
                trace_id: str,
                outputs: Dict[str, Any] = None,
                metrics: List[Dict[str, Any]] = None,
                status: str = "OK",
                error: str = None) -> bool:
        """
        End a span.
        
        Args:
            span_id: Span ID to end
            trace_id: Trace ID this span belongs to
            outputs: Output data from the span
            metrics: List of metrics
            status: Status ("OK" or "ERROR")
            error: Error message if status is ERROR
            
        Returns:
            True if successful
        """
        event = self.create_event(
            event_type="span_end",
            trace_id=trace_id,
            span_id=span_id,
            outputs=outputs or {},
            metrics=metrics or [],
            status=status,
            error=error,
            duration_ms=None  # Duration will be calculated by the API
        )
        
        success = self.send_event(event)
        if success:
            logger.info(f"🔚 Ended span: {span_id}")
        else:
            logger.error(f"❌ Failed to end span: {span_id}")
            
        return success


# Global SDK instance for convenient usage
_default_sdk = None

def get_default_sdk() -> SimpleMLObservabilitySDK:
    """Get or create the default SDK instance."""
    global _default_sdk
    if _default_sdk is None:
        _default_sdk = SimpleMLObservabilitySDK()
    return _default_sdk

def configure_sdk(api_base_url: str = DEFAULT_API_BASE_URL, 
                 api_endpoint: str = DEFAULT_API_ENDPOINT,
                 timeout: int = 30):
    """
    Configure the default SDK instance.
    
    Args:
        api_base_url: Base URL of the Genesis API server
        api_endpoint: API endpoint for sending events
        timeout: Request timeout in seconds
    """
    global _default_sdk
    _default_sdk = SimpleMLObservabilitySDK(
        api_base_url=api_base_url,
        api_endpoint=api_endpoint,
        timeout=timeout
    )

# Convenience functions using the default SDK
def start_trace(name: str,
               inputs: Dict[str, Any] = None,
               attributes: Dict[str, Any] = None) -> str:
    """Start a trace using the default SDK."""
    return get_default_sdk().start_trace(name, inputs, attributes)

def end_trace(trace_id: str,
             outputs: Dict[str, Any] = None,
             metrics: List[Dict[str, Any]] = None,
             status: str = "OK",
             error: str = None) -> bool:
    """End a trace using the default SDK."""
    return get_default_sdk().end_trace(trace_id, outputs, metrics, status, error)

def start_span(name: str,
              trace_id: str,
              span_type: str = "STEP",
              parent_span_id: str = None,
              inputs: Dict[str, Any] = None,
              attributes: Dict[str, Any] = None) -> str:
    """Start a span using the default SDK."""
    return get_default_sdk().start_span(name, trace_id, span_type, parent_span_id, inputs, attributes)

def end_span(span_id: str,
            trace_id: str,
            outputs: Dict[str, Any] = None,
            metrics: List[Dict[str, Any]] = None,
            status: str = "OK",
            error: str = None) -> bool:
    """End a span using the default SDK."""
    return get_default_sdk().end_span(span_id, trace_id, outputs, metrics, status, error)

# LLM monitoring helper functions
def monitor_llm_call(trace_id: str,
                    parent_span_id: str = None,
                    model: str = "gpt-4",
                    provider: str = "openai",
                    messages: List[Dict[str, Any]] = None,
                    response: str = "",
                    input_tokens: int = 0,
                    output_tokens: int = 0,
                    **kwargs) -> str:
    """
    Monitor an LLM call by creating a span with LLM-specific data.
    
    Args:
        trace_id: Trace ID this LLM call belongs to
        parent_span_id: Parent span ID
        model: Model name (e.g., "gpt-4", "claude-3")
        provider: Provider name (e.g., "openai", "anthropic")
        messages: List of messages sent to the LLM
        response: Response from the LLM
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        **kwargs: Additional parameters
        
    Returns:
        Generated span ID for the LLM call
    """
    span_id = start_span(
        name=f"{provider}_{model}_call",
        trace_id=trace_id,
        span_type="TOOL",  # Using TOOL since LLM type doesn't exist
        parent_span_id=parent_span_id,
        inputs={
            "model": model,
            "provider": provider,
            "messages": messages or [],
            **kwargs
        },
        attributes={
            "provider": provider,
            "model_family": model.split('-')[0] if '-' in model else model,
            "api_type": "chat_completion"
        }
    )
    
    # Create metrics for token usage
    metrics = []
    if input_tokens > 0:
        metrics.append({"name": "llm_tokens_input", "value": input_tokens})
    if output_tokens > 0:
        metrics.append({"name": "llm_tokens_output", "value": output_tokens})
    if input_tokens > 0 or output_tokens > 0:
        metrics.append({"name": "llm_tokens_total", "value": input_tokens + output_tokens})
    
    # End the span with LLM response data
    end_span(
        span_id=span_id,
        trace_id=trace_id,
        outputs={
            "content": response,
            "model": model,
            "total_tokens": input_tokens + output_tokens,
            "finish_reason": kwargs.get("finish_reason", "stop")
        },
        metrics=metrics
    )
    
    return span_id 