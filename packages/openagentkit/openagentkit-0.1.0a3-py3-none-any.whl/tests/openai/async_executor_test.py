from openagentkit.modules.openai import AsyncOpenAIAgent
from openagentkit.core.tools.base_tool import tool
from pydantic import BaseModel
import asyncio
import openai
import os

class ResponseSchema(BaseModel):
    reasoning: str
    """
    The reasoning behind the response.
    """
    response: str
    """
    The final response to the user.
    """

# Define a tool
@tool # Wrap the function in a tool decorator to automatically create a schema
async def get_weather(city: str):
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
    agent = AsyncOpenAIAgent(
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

    generator = agent.execute(
        messages=[
            {"role": "user", "content": "What's the weather like in New York?"}
        ],
        response_schema=ResponseSchema,
    )

    async for response in generator:
        print(response)

if __name__ == "__main__":
    asyncio.run(main())