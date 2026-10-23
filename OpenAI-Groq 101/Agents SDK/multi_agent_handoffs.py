# Importing Packages
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import Agent, Runner, handoff, OpenAIChatCompletionsModel

# Load ENV Variables
load_dotenv()

# Disable tracing telemetry to prevent OpenAI auth errors
os.environ["OPENAI_TRACING_DISABLED"] = "true"



# Reason to choose a specialist by triage agent to handoff
class HandoffInput(BaseModel):
    reason: str
# Callback function to happen when the handoff is invoked”
def log_handoff(ctx, data: HandoffInput):
    print(f"\nHandoff reason: {data.reason}\n")



# Initialize AsyncOpenAI client pointing to Groq
groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Wrap model for compatibility
groq_model = OpenAIChatCompletionsModel(
    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    openai_client=groq_client
)


# Define Specialist Agents with Explicit handoff_description

# Specialist Agent #1
hardware_agent = Agent(
    name="Hardware Support",
    instructions=(
        "You are a Hardware Support Technician. Help users troubleshoot physical devices "
        "like laptops, monitors, printers, keyboards, and docks. Keep responses concise (2 sentences)."
    ),
    handoff_description="Handles physical hardware issues including laptops, monitors, docking stations, and printers.",
    model=groq_model,
)

# Specialist Agent #2
access_agent = Agent(
    name="Access Management",
    instructions=(
        "You are an Access Control Specialist. Help users with password resets, "
        "2FA setup, VPN credentials, and account lockouts. Keep responses concise (2 sentences)."
    ),
    handoff_description="Handles user account access, password resets, VPN connection setup, multi-factor authentication (2FA), and permission requests.",
    model=groq_model,
)

# Specialist Agent #3
software_agent = Agent(
    name="Software Support",
    instructions=(
        "You are a Software Support Specialist. Help users resolve crashes, installation errors, "
        "and licensing issues with applications like Slack, Zoom, and IDEs. Keep responses concise (2 sentences)."
    ),
    handoff_description="Handles desktop and web application issues, software installations, crashes, license keys, and tool configurations.",
    model=groq_model,
)


# Define Triage Agent (Infers routing from specialist descriptions)
# Groq-Open AI client expects input type and callback to be present during handoff
triage_agent = Agent(
    name="IT Service Desk Router",
    instructions=(
        "You are the central IT Helpdesk router. Analyze the user's issue "
        "and hand off to the specialist whose domain best matches the request. "
        "Provide a brief reason for the handoff."
    ),
    handoffs=[
        handoff(
            agent=hardware_agent,
            input_type=HandoffInput,
            on_handoff=log_handoff,
        ),
        handoff(
            agent=access_agent,
            input_type=HandoffInput,
            on_handoff=log_handoff,
        ),
        handoff(
            agent=software_agent,
            input_type=HandoffInput,
            on_handoff=log_handoff,
        ),
    ],
    model=groq_model,
)


# Helper function to track the list of agents involved in the complete delegation path
def get_agents_used(result, initial_agent) -> list[str]:
    chain = [initial_agent.name]

    # Check result.history or result.messages for active agent attributions
    history_items = getattr(result, "history", None) or getattr(result, "messages", [])

    for item in history_items:
        # Check if the step or message contains an agent reference
        agent_obj = getattr(item, "agent", None) or getattr(item, "agent_name", None)
        if agent_obj:
            name = agent_obj.name if hasattr(agent_obj, "name") else str(agent_obj)
            # Append only if it's a new transition in the chain
            if chain[-1] != name:
                chain.append(name)

    # Fallback: If no intermediate history items recorded a handoff, include last_agent
    if hasattr(result, "last_agent") and result.last_agent:
        final_name = result.last_agent.name
        if chain[-1] != final_name:
            chain.append(final_name)

    return chain


def process_service_ticket(ticket_text: str):
    print(f"\n[Incoming IT Ticket]: \"{ticket_text}\"")

    # Run the Triage Agent [which inturn calls relevant specialist agent
    result = Runner.run_sync(
        triage_agent,
        input=ticket_text
    )

    # Extract all agents used in sequence
    agent_chain = get_agents_used(result, initial_agent=triage_agent)

    print(f"  ├─ Complete Agent Path: {' -> '.join(agent_chain)}")
    print(f"  └─ Resolution Output:\n{result.final_output}\n")


def main():
    print("--- IT Helpdesk Auto-Routing Demo ---")

    # Ticket 1: Matches Access Specialist description
    process_service_ticket("I got locked out of my account after entering the wrong 2FA code.")

    # Ticket 2: Matches Hardware Specialist description
    process_service_ticket("My external monitor keeps flickering and going black when plugged into the dock.")

    # Ticket 3: Matches Software Specialist description
    process_service_ticket("VS Code crashes every time I try to launch the Python debugger.")


if __name__ == "__main__":
    main()