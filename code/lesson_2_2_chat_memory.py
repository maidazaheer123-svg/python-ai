
"""
Task 2.2: Personal Tutor with Memory

This chatbot remembers the conversation using a messages list.
It keeps the system instruction and the latest 8 messages.

Why? To give the AI memory without sending the entire conversation
again and again.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Create the AI model
llm = ChatOllama(
    model="gemma3:1b",
    temperature=0.2
)

# Maximum conversation messages to remember
MAX_MESSAGES = 8

# System message: tells AI its role and answer length
messages = [
    SystemMessage(
        content="You are a friendly personal tutor. Give short and simple answers."
    )
]

# Store only user questions (stretch requirement)
questions = []

print("Tutor: Ask me anything. Commands: /reset, /count, bye")

while True:

    # Take input from the user
    user_input = input("You: ").strip()

    # Exit command
    if user_input.lower() == "bye":
        print("Tutor: Goodbye!")

        print("Total questions asked:", len(questions))

        if questions:
            print("First question:", questions[0])
            print("Last question:", questions[-1])

        break

    # Reset memory but keep system message
    if user_input.lower() == "/reset":
        messages = [messages[0]]
        questions = []
        print("Tutor: Memory cleared.")
        continue

    # Count messages in memory
    if user_input.lower() == "/count":
        print(f"Tutor: {len(messages)} messages in memory.")
        continue

    # Save user's question
    questions.append(user_input)

    # Add user message to conversation
    messages.append(HumanMessage(content=user_input))

    # Send conversation history to AI
    response = llm.invoke(messages)

    # Get AI's reply
    ai_reply = response.content

    print("Tutor:", ai_reply)

    # Save AI reply in conversation history
    messages.append(AIMessage(content=ai_reply))

    # Print input tokens sent to AI
    usage = response.usage_metadata
    input_tokens = usage["input_tokens"]
    print(f"(tokens sent: {input_tokens})")

    # Keep system message + latest 8 conversation messages
    # Why? To control memory and token cost.
    messages = [messages[0]] + messages[1:][-MAX_MESSAGES:]
