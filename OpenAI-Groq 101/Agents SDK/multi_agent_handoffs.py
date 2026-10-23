# Importing Packages
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (Agent, Runner, handoff, OpenAIChatCompletionsModel,
                    GuardrailFunctionOutput, input_guardrail, InputGuardrailTripwireTriggered)

from agent_utils import HandoffInput, log_handoff, TicketCheck, get_agents_used
from agent_instructions import (HARDWARE_SUPPORT_INSTRUCTIONS,
                                ACCESS_MANAGEMENT_INSTRUCTIONS,
                                SOFTWARE_SUPPORT_INSTRUCTIONS,
                                TICKET_CHECKER_INSTRUCTIONS,
                                IT_SUPPORT_INSTRUCTIONS)

# Load ENV Variables
load_dotenv()

# Disable tracing telemetry to prevent OpenAI auth errors
os.environ["OPENAI_TRACING_DISABLED"] = "true"

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
    instructions=HARDWARE_SUPPORT_INSTRUCTIONS,
    handoff_description="Handles physical hardware issues including laptops, monitors, docking stations, and printers.",
    model=groq_model,
)

# Specialist Agent #2
access_agent = Agent(
    name="Access Management",
    instructions=ACCESS_MANAGEMENT_INSTRUCTIONS,
    handoff_description="Handles user account access, password resets, VPN connection setup, multi-factor authentication (2FA), and permission requests.",
    model=groq_model,
)

# Specialist Agent #3
software_agent = Agent(
    name="Software Support",
    instructions=SOFTWARE_SUPPORT_INSTRUCTIONS,
    handoff_description="Handles desktop and web application issues, software installations, crashes, license keys, and tool configurations.",
    model=groq_model,
)

# This agent's ONLY job is to check if it is a valid request for ticket to be created
ticket_checker = Agent(
    name="Ticket Checker",
    instructions= TICKET_CHECKER_INSTRUCTIONS,
    model=groq_model
)


@input_guardrail
async def service_request_guardrail(ctx, agent, user_input):
    """Only allow IT service requests through."""
    result = await Runner.run(ticket_checker, user_input, context=ctx.context)
    # Convert the JSON string into a Pydantic object
    final = TicketCheck.model_validate_json(result.final_output)

    return GuardrailFunctionOutput(
        output_info={"reasoning": final.reasoning},
        tripwire_triggered=not final.is_on_topic,  # Block if NOT IT service request
    )


# Define Triage Agent (Infers routing from specialist descriptions)
# Triage agent stops, if it is out-of-scope request
# Groq-Open AI client expects input type and callback to be present during handoff
triage_agent = Agent(
    name="IT Service Desk Router",
    instructions=IT_SUPPORT_INSTRUCTIONS,
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
    input_guardrails=[service_request_guardrail],
    model=groq_model,
)




def process_service_ticket(ticket_text: str):
    result = None
    print(f"\n[Incoming IT Ticket]: \"{ticket_text}\"")

    try:
        # Run the Triage Agent [which inturn calls relevant specialist agent]
        result = Runner.run_sync(
            triage_agent,
            input=ticket_text
        )
    except InputGuardrailTripwireTriggered as err: # Exception raised for irrelevant queries
        print("\nGuardrail triggered!")
        print("\nReasoning:", err.guardrail_result.output.output_info["reasoning"])

    # Extract all agents used in sequence (if valid ticket request raised)
    if result:
        agent_chain = get_agents_used(result, initial_agent=triage_agent)

        print(f"  ├─ Complete Agent Path: {' -> '.join(agent_chain)}")
        print(f"  └─ Resolution Output:\n{result.final_output}\n")


if __name__ == "__main__":
    print("--- IT Helpdesk Auto-Routing Demo ---")

    # Ticket 1: Matches Access Specialist description
    # process_service_ticket("I got locked out of my account after entering the wrong 2FA code.")

    # Ticket 2: Matches Hardware Specialist description
    # process_service_ticket("My external monitor keeps flickering and going black when plugged into the dock.")

    # Ticket 3: Matches Software Specialist description
    # process_service_ticket("VS Code crashes every time I try to launch the Python debugger.")

    # Ticket 4: Irrelevant request
    process_service_ticket("How is the weather in Chennai right now?")