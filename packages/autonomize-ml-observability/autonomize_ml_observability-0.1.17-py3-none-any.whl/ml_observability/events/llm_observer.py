"""
LLM Observer for tracking and monitoring LLM client calls.

This module provides observability capabilities for LLM clients. It wraps LLM clients
and produces appropriate events for both standalone LLM calls and agent-integrated calls.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timezone

from ..simple_sdk import get_default_sdk
from .schemas import EventType, SpanType
from ..observability.cost_tracking import get_cost_tracker, CostTracker

logger = logging.getLogger(__name__)

class LLMObserver:
    """
    LLM Observer that wraps LLM clients and produces events.
    
    This class handles two contexts:
    1. Standalone LLM calls - Creates trace_start/end events
    2. Agent-integrated calls - Creates span_start/end events with parent
    """
    
    def __init__(self, client: Any, provider: str):
        """
        Initialize the LLM Observer.
        
        Args:
            client: The LLM client to wrap
            provider: Provider name (openai, azure_openai, anthropic)
        """
        self.client = client
        self.provider = provider
        self.cost_tracker = get_cost_tracker()
        self.sdk = get_default_sdk()  # Get the Simple SDK instance
        self._wrap_client_methods()
        
        # Track running totals for the session
        self._session_totals = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
            "calls": 0
        }
        
        logger.debug(f"✅ Initialized LLM Observer for {provider} with fresh session totals")
    
    def _wrap_client_methods(self):
        """Wrap appropriate client methods based on provider."""
        if self.provider in ["openai", "azure_openai"]:
            if hasattr(self.client.chat, "completions") and hasattr(self.client.chat.completions, "create"):
                original_create = self.client.chat.completions.create
                
                def wrapped_create(*args, **kwargs):
                    return self._handle_openai_call(original_create, *args, **kwargs)
                
                self.client.chat.completions.create = wrapped_create
                
        elif self.provider == "anthropic":
            if hasattr(self.client, "messages") and hasattr(self.client.messages, "create"):
                original_create = self.client.messages.create
                
                def wrapped_create(*args, **kwargs):
                    return self._handle_anthropic_call(original_create, *args, **kwargs)
                
                self.client.messages.create = wrapped_create
                
        logger.debug(f"✅ Wrapped {self.provider} client methods for LLM observation")
    
    def _extract_openai_metrics(self, result: Any, model: str) -> List[Dict[str, Any]]:
        """Extract token and cost metrics from OpenAI API response."""
        # Get token metrics
        prompt_tokens = result.usage.prompt_tokens
        completion_tokens = result.usage.completion_tokens
        total_tokens = result.usage.total_tokens
        
        logger.debug(f"\n🔍 Token Usage for {model}:")
        logger.debug(f"  • Input Tokens:   {prompt_tokens:,}")
        logger.debug(f"  • Output Tokens:  {completion_tokens:,}")
        logger.debug(f"  • Total Tokens:   {total_tokens:,}")
        
        token_metrics = [
            {"name": "llm_tokens_input", "value": prompt_tokens},
            {"name": "llm_tokens_output", "value": completion_tokens},
            {"name": "llm_tokens_total", "value": total_tokens}
        ]
        
        # Track costs using CostTracker
        cost_entry = self.cost_tracker.track_cost(
            model_name=model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            provider=self.provider,
            log_to_mlflow=False  # We'll handle metrics via events
        )
        
        logger.debug(f"\n💰 Cost Breakdown for {model}:")
        logger.debug(f"  • Input Cost:    ${cost_entry['input_cost']:.6f}")
        logger.debug(f"  • Output Cost:   ${cost_entry['output_cost']:.6f}")
        logger.debug(f"  • Total Cost:    ${cost_entry['total_cost']:.6f}")
        
        # Add cost metrics
        cost_metrics = [
            {"name": "llm_cost_input", "value": cost_entry["input_cost"]},
            {"name": "llm_cost_output", "value": cost_entry["output_cost"]},
            {"name": "llm_cost_total", "value": cost_entry["total_cost"]}
        ]
        
        # Update session totals
        self._session_totals["input_tokens"] += prompt_tokens
        self._session_totals["output_tokens"] += completion_tokens
        self._session_totals["total_tokens"] += total_tokens
        self._session_totals["input_cost"] += cost_entry["input_cost"]
        self._session_totals["output_cost"] += cost_entry["output_cost"]
        self._session_totals["total_cost"] += cost_entry["total_cost"]
        self._session_totals["calls"] += 1
        
        logger.debug(f"\n📊 Running Session Totals:")
        logger.debug(f"  • Total Calls:       {self._session_totals['calls']:,}")
        logger.debug(f"  • Total Input Tokens:  {self._session_totals['input_tokens']:,}")
        logger.debug(f"  • Total Output Tokens: {self._session_totals['output_tokens']:,}")
        logger.debug(f"  • Total Tokens:        {self._session_totals['total_tokens']:,}")
        logger.debug(f"  • Total Input Cost:    ${self._session_totals['input_cost']:.6f}")
        logger.debug(f"  • Total Output Cost:   ${self._session_totals['output_cost']:.6f}")
        logger.debug(f"  • Total Cost:          ${self._session_totals['total_cost']:.6f}")
        
        return token_metrics + cost_metrics
    
    def _extract_anthropic_metrics(self, result: Any, model: str) -> List[Dict[str, Any]]:
        """Extract token and cost metrics from Anthropic API response."""
        # Get token metrics
        input_tokens = result.usage.input_tokens
        output_tokens = result.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        
        token_metrics = [
            {"name": "llm_tokens_input", "value": input_tokens},
            {"name": "llm_tokens_output", "value": output_tokens},
            {"name": "llm_tokens_total", "value": total_tokens}
        ]
        
        # Track costs using CostTracker
        cost_entry = self.cost_tracker.track_cost(
            model_name=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=self.provider,
            log_to_mlflow=False  # We'll handle metrics via events
        )
        
        # Add cost metrics
        cost_metrics = [
            {"name": "llm_cost_input", "value": cost_entry["input_cost"]},
            {"name": "llm_cost_output", "value": cost_entry["output_cost"]},
            {"name": "llm_cost_total", "value": cost_entry["total_cost"]}
        ]
        
        return token_metrics + cost_metrics
    
    def _handle_openai_call(self, original_func, *args, **kwargs):
        """Handle OpenAI/Azure OpenAI call with event production."""
        # Extract key info
        model = kwargs.get("model", "gpt-3.5-turbo")
        messages = kwargs.get("messages", [])
        parent_id = kwargs.pop("parent_span_id", None)
        trace_id = kwargs.pop("trace_id", None)
        
        logger.debug(f"\n🚀 Starting LLM call for {model}:")
        logger.debug(f"  • Parent Span: {parent_id or 'None'}")
        logger.debug(f"  • Trace ID:    {trace_id or 'New trace'}")
        
        try:
            # Start trace/span based on context
            if parent_id:
                # Context 2: Part of agent trace
                span_id = str(uuid.uuid4())
                logger.debug(f"  • Creating child span: {span_id}")
                
                # Use SDK's start_span
                span_id = self.sdk.start_span(
                    name="llm_call",
                    trace_id=trace_id,
                    span_type=SpanType.TOOL,
                    parent_span_id=parent_id,
                    inputs={
                        "model": model,
                        "provider": self.provider,
                        "messages": self._sanitize_messages(messages),
                        "temperature": kwargs.get("temperature", 1.0),
                        "max_tokens": kwargs.get("max_tokens")
                    }
                )
            else:
                # Context 1: Standalone LLM call
                trace_id = str(uuid.uuid4())
                trace_name = f"llm_call_{model}"  # Store name for reuse
                logger.debug(f"  • Creating new trace: {trace_id}")
                
                # Use SDK's start_trace
                trace_id = self.sdk.start_trace(
                    name=trace_name,
                    inputs={
                        "model": model,
                        "provider": self.provider,
                        "messages": self._sanitize_messages(messages),
                        "temperature": kwargs.get("temperature", 1.0),
                        "max_tokens": kwargs.get("max_tokens")
                    }
                )
            
            # Make actual API call
            start_time = datetime.now(timezone.utc)
            result = original_func(*args, **kwargs)
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            logger.debug(f"\n⏱️  API Call Duration: {duration_ms:.2f}ms")
            
            # Extract metrics including costs
            metrics = self._extract_openai_metrics(result, model)
            
            # Send end event based on context
            if parent_id:
                # Use SDK's end_span
                self.sdk.end_span(
                    span_id=span_id,
                    trace_id=trace_id,
                    outputs={
                        "content": result.choices[0].message.content,
                        "finish_reason": result.choices[0].finish_reason,
                        "model": model,
                        "total_tokens": result.usage.total_tokens,
                        "cost_info": {  # Add cost info to outputs
                            "input_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_input"),
                            "output_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_output"),
                            "total_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_total")
                        }
                    },
                    metrics=metrics,
                    status="OK"
                )
            else:
                # Use SDK's end_trace
                self.sdk.end_trace(
                    trace_id=trace_id,
                    outputs={
                        "content": result.choices[0].message.content,
                        "finish_reason": result.choices[0].finish_reason,
                        "model": model,
                        "total_tokens": result.usage.total_tokens,
                        "cost_info": {  # Add cost info to outputs
                            "input_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_input"),
                            "output_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_output"),
                            "total_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_total")
                        }
                    },
                    metrics=metrics,  # Add metrics to standalone LLM calls
                    status="OK"
                )
            
            logger.debug(f"\n✅ LLM call completed successfully")
            return result
            
        except Exception as e:
            # Handle errors with appropriate events
            error_msg = str(e)
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            if parent_id:
                self.sdk.end_span(
                    span_id=span_id,
                    trace_id=trace_id,
                    outputs={"error": error_msg},
                    status="ERROR",
                    error=error_msg
                )
            else:
                self.sdk.end_trace(
                    trace_id=trace_id,
                    outputs={"error": error_msg},
                    status="ERROR",
                    error=error_msg
                )
            
            raise
    
    def _handle_anthropic_call(self, original_func, *args, **kwargs):
        """Handle Anthropic call with event production."""
        # Extract key info
        model = kwargs.get("model", "claude-2")
        messages = kwargs.get("messages", [])
        parent_id = kwargs.pop("parent_span_id", None)
        trace_id = kwargs.pop("trace_id", None)
        
        logger.debug(f"\n🚀 Starting LLM call for {model}:")
        logger.debug(f"  • Parent Span: {parent_id or 'None'}")
        logger.debug(f"  • Trace ID:    {trace_id or 'New trace'}")
        
        try:
            # Start trace/span based on context
            if parent_id:
                # Context 2: Part of agent trace
                span_id = str(uuid.uuid4())
                logger.debug(f"  • Creating child span: {span_id}")
                
                # Use SDK's start_span
                span_id = self.sdk.start_span(
                    name="llm_call",
                    trace_id=trace_id,
                    span_type=SpanType.TOOL,
                    parent_span_id=parent_id,
                    inputs={
                        "model": model,
                        "provider": self.provider,
                        "messages": self._sanitize_messages(messages),
                        "temperature": kwargs.get("temperature", 1.0),
                        "max_tokens": kwargs.get("max_tokens")
                    }
                )
            else:
                # Context 1: Standalone LLM call
                trace_id = str(uuid.uuid4())
                trace_name = f"llm_call_{model}"  # Store name for reuse
                logger.debug(f"  • Creating new trace: {trace_id}")
                
                # Use SDK's start_trace
                trace_id = self.sdk.start_trace(
                    name=trace_name,
                    inputs={
                        "model": model,
                        "provider": self.provider,
                        "messages": self._sanitize_messages(messages),
                        "temperature": kwargs.get("temperature", 1.0),
                        "max_tokens": kwargs.get("max_tokens")
                    }
                )
            
            # Make actual API call
            start_time = datetime.now(timezone.utc)
            result = original_func(*args, **kwargs)
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            logger.debug(f"\n⏱️  API Call Duration: {duration_ms:.2f}ms")
            
            # Extract metrics including costs
            metrics = self._extract_anthropic_metrics(result, model)
            
            # Send end event based on context
            if parent_id:
                # Use SDK's end_span
                self.sdk.end_span(
                    span_id=span_id,
                    trace_id=trace_id,
                    outputs={
                        "content": result.content[0].text,
                        "finish_reason": result.stop_reason,
                        "model": model,
                        "total_tokens": result.usage.input_tokens + result.usage.output_tokens,
                        "cost_info": {  # Add cost info to outputs
                            "input_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_input"),
                            "output_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_output"),
                            "total_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_total")
                        }
                    },
                    metrics=metrics,
                    status="OK"
                )
            else:
                # Use SDK's end_trace
                self.sdk.end_trace(
                    trace_id=trace_id,
                    outputs={
                        "content": result.content[0].text,
                        "finish_reason": result.stop_reason,
                        "model": model,
                        "total_tokens": result.usage.input_tokens + result.usage.output_tokens,
                        "cost_info": {  # Add cost info to outputs
                            "input_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_input"),
                            "output_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_output"),
                            "total_cost": next(m["value"] for m in metrics if m["name"] == "llm_cost_total")
                        }
                    },
                    metrics=metrics,  # Add metrics to standalone LLM calls
                    status="OK"
                )
            
            logger.debug(f"\n✅ LLM call completed successfully")
            return result
            
        except Exception as e:
            # Handle errors with appropriate events
            error_msg = str(e)
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            if parent_id:
                self.sdk.end_span(
                    span_id=span_id,
                    trace_id=trace_id,
                    outputs={"error": error_msg},
                    status="ERROR",
                    error=error_msg
                )
            else:
                self.sdk.end_trace(
                    trace_id=trace_id,
                    outputs={"error": error_msg},
                    status="ERROR",
                    error=error_msg
                )
            
            raise
    
    def _sanitize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize messages for event logging."""
        sanitized = []
        for msg in messages:
            sanitized_msg = msg.copy()
            if "content" in sanitized_msg and isinstance(sanitized_msg["content"], str):
                if len(sanitized_msg["content"]) > 1000:
                    sanitized_msg["content"] = sanitized_msg["content"][:1000] + "..."
            sanitized.append(sanitized_msg)
        return sanitized

def create_llm_observer(
    client: Any,
    provider: Optional[str] = None,
) -> LLMObserver:
    """
    Create an LLM observer for a client.
    
    Args:
        client: The LLM client to observe
        provider: Optional provider name (will be auto-detected if not provided)
        
    Returns:
        LLMObserver instance
    """
    if provider is None:
        provider = _detect_provider(client)
    
    return LLMObserver(client, provider)

def _detect_provider(client: Any) -> str:
    """Detect the provider from client instance."""
    client_name = client.__class__.__name__.lower()
    
    if "azure" in client_name:
        return "azure_openai"
    elif "openai" in client_name:
        return "openai"
    elif "anthropic" in client_name:
        return "anthropic"
    else:
        # Fallback to module-based detection
        mod = client.__class__.__module__.lower()
        if "openai" in mod and "azure" in mod:
            return "azure_openai"
        elif "openai" in mod:
            return "openai"
        elif "azure" in mod:
            return "azure_openai"
        elif "anthropic" in mod:
            return "anthropic"
        else:
            logger.warning(f"Could not determine provider for client {client.__class__.__name__}")
            return "unknown" 