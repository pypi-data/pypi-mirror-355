# Autonomize ML Observability SDK

A lightweight SDK for monitoring, tracing, and tracking costs for LLM applications with a focus on simplicity and direct HTTP communication.

## Features

- **LLM Monitoring**: Automatically monitor OpenAI, Azure OpenAI, and Anthropic API calls
- **Cost Tracking**: Track token usage and costs across different models and providers
- **Direct HTTP Integration**: Send events directly to Genesis API without intermediaries
- **Enhanced Agent Tracing**: Monitor and track multi-step agent workflows with proper parent-child relationships
- **Accurate Duration Tracking**: Precise timing for all spans and traces
- **Automatic Provider Detection**: Auto-detects LLM provider from client instance
- **Simple Event Types**: Streamlined event schemas for traces and spans

## Installation

Install the package using pip:

```bash
pip install autonomize-ml-observability
```

### With Provider-Specific Dependencies

```bash
# For OpenAI support
pip install "autonomize-ml-observability[openai]"

# For Anthropic support
pip install "autonomize-ml-observability[anthropic]"

# For Azure OpenAI support
pip install "autonomize-ml-observability[azure]"
```

## Quick Start

### Basic LLM Call Monitoring

```python
import os
from openai import AzureOpenAI
from ml_observability.events.llm_observer import create_llm_observer
from ml_observability.simple_sdk import configure_sdk

# Configure SDK to point to Genesis API
configure_sdk(api_base_url="http://localhost:8001")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("OPENAI_API_BASE_ENDPOINT")
)

# Create and store the observer (provider will be auto-detected)
llm_observer = create_llm_observer(client)

# Use the client as normal - monitoring happens automatically
response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"}
    ]
)

print(response.choices[0].message.content)
```

## Example Workflows

### 1. Single LLM Call

The simplest example showing basic LLM monitoring:

```python
from ml_observability.simple_sdk import configure_sdk, start_trace, end_trace
from ml_observability.events.llm_observer import create_llm_observer

# Configure SDK
configure_sdk(api_base_url="http://localhost:8001")

# Initialize client and observer
client = init_azure_client()
llm_observer = create_llm_observer(client)

# Start trace
trace_id = start_trace(
    name="single_llm_call",
    inputs={"query": "What is machine learning?"}
)

# Make LLM call (automatically monitored)
response = client.chat.completions.create(
    model=deployment,
    messages=[...],
    temperature=0.7
)

# End trace
end_trace(trace_id, outputs={"response": response.choices[0].message.content})
```

### 2. Two-Step Agent

Example of a two-step agent workflow with proper tracing:

```python
from ml_observability.simple_sdk import (
    start_trace, start_span, end_span, end_trace
)

# Start trace
trace_id = start_trace(name="two_step_agent")

# Step 1: Generate questions
step1_span_id = start_span(
    name="generate_question",
    trace_id=trace_id,
    span_type="STEP"
)

# Make first LLM call
response1 = client.chat.completions.create(...)
end_span(step1_span_id, outputs={"questions": response1.choices[0].message.content})

# Step 2: Generate answers
step2_span_id = start_span(
    name="generate_answers",
    trace_id=trace_id,
    span_type="STEP",
    parent_span_id=step1_span_id
)

# Make second LLM call
response2 = client.chat.completions.create(...)
end_span(step2_span_id, outputs={"answers": response2.choices[0].message.content})

# End trace
end_trace(trace_id)
```

### 3. Complex Agent Workflow

Example of a multi-step agent with preparation, outline generation, and explanation:

```python
# Start trace
trace_id = start_trace(name="complex_agent")

# Step 1: Preparation
step1_span_id = start_span(
    name="prepare_input",
    trace_id=trace_id,
    span_type="STEP"
)
# Process input...
end_span(step1_span_id, outputs={"processed_query": processed_query})

# Step 2: Generate outline
step2_span_id = start_span(
    name="generate_outline",
    trace_id=trace_id,
    span_type="STEP",
    parent_span_id=step1_span_id
)
# Generate outline with LLM...
end_span(step2_span_id, outputs={"outline": outline})

# Step 3: Generate explanation
step3_span_id = start_span(
    name="generate_explanation",
    trace_id=trace_id,
    span_type="STEP",
    parent_span_id=step2_span_id
)
# Generate explanation with LLM...
end_span(step3_span_id, outputs={"explanation": explanation})

# End trace
end_trace(trace_id)
```

## Event Types

The SDK uses two simple event types:

1. `EventType`:
   - `TRACE_START`: Start of a trace
   - `TRACE_END`: End of a trace
   - `SPAN_START`: Start of a span
   - `SPAN_END`: End of a span

2. `SpanType`:
   - `STEP`: A general processing step
   - `TOOL`: A tool or external service call
   - `AGENT`: An agent action or decision

## Architecture

The SDK follows a simple architecture:

1. **Simple SDK**: Core component that sends events via HTTP to Genesis API
2. **LLM Observer**: Wraps LLM clients and produces events automatically
3. **Cost Tracking**: Tracks token usage and costs across providers
4. **Event Types**: Simple enums for trace and span lifecycle events

All events are sent directly to the Genesis API via HTTP, with no intermediate message queues or workers.