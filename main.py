# Importing Packages
import os
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_mcp_adapters.client import MultiServerMCPClient
from custom_local_tools import add, subtract, multiply, divide

# Load ENV Variables
load_dotenv()

# Initialize the model (picks up GROQ_API_KEY and GROQ_MODEL from environment)
llm_model = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
                     temperature=0.7) # Lower the temperature, more factual

def build_naive_math_agent(question):

    # Combine all tools into a list
    tools = [add, subtract, multiply, divide]

    # Create the agent
    naive_math_agent = create_agent(
        model=llm_model,
        tools=tools,
    )

    # Invoke the agent
    result = naive_math_agent.invoke({
        "messages": [("user", question)]
    })

    return result


async def build_mcp_news_agent():
    """
        Main async function — MCP connections are async because
        they involve I/O (spawning processes, network calls).
    """

    # Defining absolute path of the mcp server
    current_dir = os.path.dirname(os.path.abspath(__file__))
    news_server_path = os.path.join(current_dir, "mcp_news_server.py")

    client = MultiServerMCPClient(
        {
            # Creating a client for News MCP server
            "mcp_news_server": {
                "command": "python",
                "args": [news_server_path],
                "transport": "stdio",  # Local child process (stdin/stdout)
            },
        }
    )

    print("\nAvailable Tools [News Categories]")
    tools = await client.get_tools() #  MCP Tools transformed to LangChain tools

    category = 1
    for t in tools:
        print(f"  {category}.{t.name}")
        category += 1

    # Creating the News agent - Async
    question = input("\nEnter your news preference: ")
    news_agent = create_agent(llm_model, tools=tools)
    news = await news_agent.ainvoke({
        "messages": [("user", question)]
    })
    print("\n")
    print(news['messages'][-1].content)


def run_langchain_sandbox(choice, user_input):

    if choice == 1:
        # Sample Model Invocation
        response = llm_model.invoke([HumanMessage(content=user_input)])
        print("\n")
        print(response.content)
        print("\n")

    elif choice == 2:
        # Creating prompts with ChatPromptTemplate
        chat_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful coding tutor. Keep answers short and clear."),
            ("human", "Explain {concept} with a simple Python example."),
        ])
        # Chain construction
        chain = chat_template | llm_model | StrOutputParser()
        result = chain.invoke({"concept": user_input})
        print("\n")
        print(result)
        print("\n")

    elif choice == 3:
        # Run the naive math agent with user query
        result = build_naive_math_agent(user_input)
        print("\nAgent Execution Trace")

        if len(result["messages"]) == 2 :
            print("\nLLM probably answered directly with no tool calls")
            print("\n")

        step = 1
        for msg in result["messages"]:
            # 1. Human message = original user question
            if msg.type == "human":
                print(f"{step}. User asked:")
                print(f"   {msg.content}")
                print("\n")
                step += 1

            # 2. AI message with tool_calls
            elif msg.type == "ai" and getattr(msg, "tool_calls", None):
                for tool_call in msg.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    print(f"{step}. Agent decision:")
                    print(f"   I need to use the tool: {tool_name}")
                    print(f"   Tool input: {tool_args}")
                    print("\n")
                    step += 1

            # 3. Tool message = result returned by the tool
            elif msg.type == "tool":
                print(f"{step}. Tool observation:")
                print(f"   Tool returned: {msg.content}")
                print("\n")
                step += 1

            # 4. Final AI message
            elif msg.type == "ai" and msg.content:
                print(f"{step}. Final answer:")
                print(f"   {msg.content}")
                print("\n")
                step += 1

    elif choice == 4:
        print("\n")
        print("Retrieved the response from MCP powered News Agent")

    else:
        print("\nInvalid choice.\n")


if __name__ == "__main__":
    choice =  int(input("""
    LangChain Sandbox Options:. 
    1. Simple Model Execution
    2. Chain Model Execution - Python Expert
    3. Test a sample agent - Naive Math Agent
    4. Test an MCP powered News Agent\n
    Enter the option number to be executed: """))
    user_input = "Hello World"

    if choice == 1:
        user_input = input("""\nEnter your query: """)
    if choice == 2:
        user_input = input("""\nEnter the python topic to be explained: """)
    if choice == 3:
        user_input = input("""\nEnter a basic math query involving add, subtract, multiply, and divide: """)
    if choice == 4:
        asyncio.run(build_mcp_news_agent())
        # Sample news query: Give me 3 latest cricket news updates

    run_langchain_sandbox(choice, user_input)
