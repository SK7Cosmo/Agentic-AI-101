from os import getenv
from openai import OpenAI
from dotenv import load_dotenv


# Load ENV Variables
load_dotenv()

# Use Groq's free API key with the OpenAI SDK
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=getenv("GROQ_API_KEY")
)


def run_openai_sandbox(choice, user_input):

    if choice == 1:
        # Single turn Conversation with Responses API
        response = client.responses.create(
            model=getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            input=user_input
        )
        print("\n")
        print(response.output_text)

    elif choice == 2:

        """NOTE: This script uses OpenAI API through Groq API.
        Hence, it is not possible to maintain memory context in server side
        
        Direct OpenAI API: chaining "response.id" as "previous_response_id"
                           uses Responses API
        Third-party OpenAI-compatible APIs (Groq): chaining through messages array
                                                   uses Chat completions API"""

        # Client side context management
        messages = [{
                    "role": "system",
                    "content": "Keep the responses crisp"
                }]

        print("\n--- Multi-Turn Interactive Chat (Type 'exit' to quit) ---")
        turn = 1

        while True:
            user_input = input(f"\n[Turn {turn}] You: ").strip()

            if not user_input:
                continue

            # Handle Exit & Generate Summary
            if user_input.lower() in ["exit", "quit"]:
                print("\nEnding conversation session...")
                print("Generating conversation summary...\n")

                # Append explicit instruction to generate summary
                messages.append({
                    "role": "user",
                    "content": "I am ending the chat. Please summarize our entire conversation highlighting the main points discussed."
                })

                # Request summary from the model
                response = client.chat.completions.create(
                    model=getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                    messages=messages
                )

                summary = response.choices[0].message.content
                print(f"{summary}")
                break

            # Append user message to history
            messages.append({"role": "user", "content": user_input})

            # Call completions API endpoint
            response = client.chat.completions.create(
                model=getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                messages=messages
            )

            assistant_reply = response.choices[0].message.content
            print(f"Assistant: {assistant_reply}")
            print(f"  └─ [Context Length: {len(messages)} stored messages]")

            # Append assistant response to history to maintain multi-turn context
            messages.append({"role": "assistant", "content": assistant_reply})
            turn += 1

    else:
        print("\nInvalid choice.\n")

    return


if __name__ == "__main__":
    choice = int(input("""
      OpenAI Responses API Sandbox Options: 
      1. Single-turn chat
      2. Multi-turn Chat (Type 'exit' to quit)
      Enter the option number to be executed: """))
    user_input = "Hello World"

    if choice == 1:
        user_input = input("""\nEnter your query: """)
    elif choice == 2:
        pass

    run_openai_sandbox(choice, user_input)