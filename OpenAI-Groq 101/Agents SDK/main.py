# Importing Packages
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel

from custom_function_tools import search_books
from multi_agent_handoffs import process_service_ticket

# Load ENV Variables
load_dotenv()

# Disable tracing telemetry to prevent OpenAI auth errors
os.environ["OPENAI_TRACING_DISABLED"] = "true"


def execute_agent(choice, user_input):
    """
    Build and execute OpenAI-Groq agent.
    """

    # Initialize AsyncOpenAI client pointing to Groq
    groq_client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )

    # Wrap model for compatibility
    groq_model = OpenAIChatCompletionsModel(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        openai_client=groq_client
    )

    if choice == 1:
        # Define Agent passing the wrapped model object
        cricket_agent = Agent(
            name="Cric Guru",
            instructions="You are a cricket subject matter expert. Answer crisp.",
            model=groq_model
        )

        # Run the Agent
        result = Runner.run_sync(
            cricket_agent,
            input=user_input
        )

        print("\nCric Guru Response")
        print(result.final_output)

    elif choice == 2:
        # Define Agent passing the wrapped model object long with the tool(s)
        tools = [search_books]
        bookkeeper_agent = Agent(
            name="Books Guru",
            instructions="You are a book-keeper assistant. Use provided tool to answer.",
            tools=tools,
            model=groq_model
        )

        # Run the Agent
        result = Runner.run_sync(
            bookkeeper_agent,
            input=user_input
        )

        print("\nBooks Guru Response")
        print(result.final_output)

    elif choice == 3:
        process_service_ticket(user_input)

    else:
        print("\nInvalid choice.\n")

    return


if __name__ == "__main__":
    choice =  int(input("""
    OpenAI-Groq Agents Sandbox Options:. 
    1. Cric Guru - Pure OpenAI-Groq Agent
    2. Books Guru - OpenAI-Groq Agent + tool
    3. IT HelpDesk - Agent Handoffs\n
    Enter the option number to be executed: """))
    user_input = "Hello World"

    if choice == 1:
        user_input = input("\nAsk your query to the Cric Guru: ")
    elif choice == 2:
        user_input = input("\nAsk your query to the Books Guru [Book title, author name, or topic to search for.]: ")
    elif choice == 3:
        user_input = input("\nEnter the concern to create appropriate ticket: ")
        # Examples
        # 1. I got locked out of my account after entering the wrong 2FA code
        # 2. My external monitor keeps flickering and going black when plugged into the dock.
        # 3. VS Code crashes every time I try to launch the Python debugger.
        # 4. What is 2+5?
    else:
        print("\nInvalid choice.\n")

    execute_agent(choice, user_input)


# 61151273
# 61151993