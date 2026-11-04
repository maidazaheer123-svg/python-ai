"""
Task 2.2: Personal Tutor with Memory

This chatbot remembers the conversation using a messages list.
The system message is always messages[0], followed by the latest
8 conversation messages (user and assistant).

Why? To give the AI memory without sending the entire conversation
again and again, which saves tokens and keeps responses fast.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Create the AI model
llm = ChatOllama(
    model="gemma3:1b",
    temperature=0.2
)

# Why messages[0] is the system message? It tells the AI its role, and
# keeping it at index 0 makes it easy to protect from trimming and /reset.
messages = [
    SystemMessage(
        content="You are a friendly personal tutor. Give short and simple answers."
    )
]

# Why a separate list? messages also holds AI replies and the system
# message, so it can't be used to count only the user's questions.
questions = []

print("Tutor: Ask me anything. Commands: /reset, /count, bye")

while True:

    user_input = input("You: ").strip()

    # Exit command: show the stretch summary
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

    # Count messages in memory (includes the system message)
    if user_input.lower() == "/count":
        print(f"Tutor: {len(messages)} messages in memory.")
        continue

    # Save the user's question (stretch)
    questions.append(user_input)

    # Add the user message to the conversation
    messages.append(HumanMessage(content=user_input))

    # Send conversation history to AI
    response = llm.invoke(messages)
    ai_reply = response.content

    print("Tutor:", ai_reply)

    # Add the AI reply to the conversation
    messages.append(AIMessage(content=ai_reply))

    # Print the input tokens sent to the AI
    input_tokens = response.usage_metadata["input_tokens"]
    print(f"(tokens sent: {input_tokens})")

    # Why trim? Every message is re-sent on each turn, so old messages
    # increase token cost. Keep the system message + latest 8 messages.
    messages = [messages[0]] + messages[1:][-8:]