# OpenAgentKit

[![PyPI version](https://badge.fury.io/py/openagentkit.svg)](https://test.pypi.org/project/openagentkit/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A comprehensive open-source toolkit for building agentic applications. OpenAgentKit provides a unified interface to work with various LLM providers, tools, and agent frameworks.

**WARNING**: Everything here is still in development, expect many bugs and unsupported features, please feel free to contribute! 

## Features

- **Unified LLM Interface**: Consistent API across multiple LLM providers
- **Generator-based event stream**: Event-driven processing using a generator
- **Async Support**: Built-in asynchronous processing for high-performance applications
- **Tool Integration**: Pre-built tools for common agent tasks
- **Extensible Architecture**: Easily add custom models, tools, and handlers
- **Type Safety**: Comprehensive typing support with Pydantic models

## Installation

```bash
pip install openagentkit==0.1.0a1
```

## Quick Start

```python
from openagentkit.modules.openai import OpenAIExecutor
from openagentkit.core.utils.tool_wrapper import tool
from pydantic import BaseModel
from typing import Annotated
import openai
import os

# Define a tool
@tool # Wrap the function in a tool decorator to automatically create a schema
def get_weather(city: str):
    """Get the weather of a city"""

    # Actual implementation here...
    # ...

    return f"Weather in {city}: sunny, 20°C, feels like 22°C, humidity: 50%"

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Initialize LLM service
executor = OpenAIExecutor(
    client=client,
    model="gpt-4o-mini",
    system_message="""
    You are a helpful assistant that can answer questions and help with tasks.
    You are also able to use tools to get information.
    """,
    tools=[get_weather],
    temperature=0.5,
    max_tokens=100,
    top_p=1.0,
)

generator = executor.execute(
    messages=[
        {"role": "user", "content": "What's the weather like in New York?"}
    ]
)

for response in generator:
    print(response.content)
```

## Supported Integrations

- **LLM Providers**:

  - OpenAI
  - SmallestAI
  - Azure OpenAI (via OpenAI integration)
  - More coming soon!
- **Tools** *(Mostly for prototyping purposes)*:

  - Weather information *(Requires WEATHERAPI_API_KEY)*
  - Search capabilities *(Requires TAVILY_API_KEY)*

## Architecture

OpenAgentKit is built with a modular architecture:

- **Interfaces**: Abstract base classes defining the contract for all implementations
- **Models**: Pydantic models for type-safe data handling
- **Modules**: Implementation of various services and integrations
- **Handlers**: Processors for tools and other extensions
- **Utils**: Helper functions and utilities

## Advanced Usage

### Asynchronous Processing

```python
from openagentkit.modules.openai import AsyncOpenAIExecutor
from openagentkit.core.utils.tool_wrapper import tool
from pydantic import BaseModel
from typing import Annotated
import asyncio
import openai
import os

# Define a tool
@tool # Wrap the function in a tool decorator to automatically create a schema
def get_weather(city: str):
    """Get the weather of a city"""

    # Actual implementation here...
    # ...

    return f"Weather in {city}: sunny, 20°C, feels like 22°C, humidity: 50%"

# Initialize OpenAI client
client = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

async def main():
    # Initialize LLM service
    executor = AsyncOpenAIExecutor(
        client=client,
        model="gpt-4o-mini",
        system_message="""
        You are a helpful assistant that can answer questions and help with tasks.
        You are also able to use tools to get information.
        """,
        tools=[get_weather],
        temperature=0.5,
        max_tokens=100,
        top_p=1.0,
    )

    generator = executor.execute(
        messages=[
            {"role": "user", "content": "What's the weather like in New York?"}
        ]
    )

    async for response in generator:
        print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Tool Integration

```python
from openagentkit.core.utils.tool_wrapper import tool
from pydantic import BaseModel
from typing import Annotated

# Define a tool
@tool # Wrap the function in a tool decorator to automatically create a schema
def get_weather(city: str):
    """Get the weather of a city""" # Always try to add pydoc in the function for better comprehension by LLM 

    # Actual implementation here...
    # ...

    return f"Weather in {city}: sunny, 20°C, feels like 22°C, humidity: 50%"

# Get the tool schema
print(get_weather.schema)

# Run the tool like any other function
weather_response = get_weather("Hanoi")
print(weather_response) 
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the `LICENSE` file for details.
