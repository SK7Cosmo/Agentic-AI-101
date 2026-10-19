import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from sqlalchemy.orm import clsregistry

load_dotenv()

# 1. Disable tracing to stop 401 warnings
os.environ["OPENAI_TRACING_DISABLED"] = "true"

# 2. Initialize AsyncOpenAI client pointing to Groq
groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# 3. Wrap Groq model inside OpenAIChatCompletionsModel to strip incompatible OpenAI fields
groq_model = OpenAIChatCompletionsModel(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    openai_client=groq_client
)

# 4. Define Agent passing the wrapped model object
tutor_agent = Agent(
    name="Tutor",
    instructions="You are a helpful Python tutor. Answer concisely in 2 sentences.",
    model=groq_model
)

async def main():
    result = await Runner.run(
        tutor_agent,
        input="Explain Python list comprehensions."
    )

    print("Agent Response:\n")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())