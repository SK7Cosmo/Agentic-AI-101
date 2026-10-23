# Importing Packages
from pydantic import BaseModel, Field


# These 2 functions are syntactically needed during handoff for Groq API check to pass
# Reason to choose a specialist by triage agent to handoff
class HandoffInput(BaseModel):
    reason: str
# Callback function to happen when the handoff is invoked”
def log_handoff(ctx, data: HandoffInput):
    print(f"\nHandoff reason: {data.reason}\n")


class TicketCheck(BaseModel):
    """Structured output for the guardrail checker."""

    is_on_topic: bool = Field(
        ...,
        description=(
            "True if the message reports an IT issue or asks for support"
            " falling under Access, Hardware, or Software. False otherwise."
        ),
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of why the message was approved or blocked.",
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


