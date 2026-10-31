
"""
Lesson 2.3: Persona Bot with Real Facts

This chatbot answers bakery questions using stored business facts.
It supports different personalities, conversation memory,
direct price lookup, and adding new menu items.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


# 1. BUSINESS FACTS
facts = {
    "business_name": "Sweet Cravings Diaries",
    "business_type": "Home bakery",
    "location": "Lahore, Pakistan",
    "platform": "Instagram: sweet.cravings3",
    "delivery": "Contact us on Instagram for order details",

    "prices": {
        "brownie": 270,
        "cupcake": 300,
        "1 lb vanilla cake": 1400,
        "1 lb chocolate cream cake": 1600,
        "1 lb double chocolate cake": 1800,
        "2 lb vanilla cake": 2000,
        "2 lb chocolate cream cake": 2200,
        "2 lb double chocolate cake": 2500
    }
}


# 2. PERSONAS
personas = {
    "friendly": "You are warm, friendly and cheerful. Use simple words.",
    "formal": "You are polite and professional. Use formal language.",
    "sales": "You are excited and persuasive. Suggest one extra menu item when relevant."
}


# 3. CONFIGURATION
config = {
    "model": "gemma3:1b",
    "temperature": 0.2,
    "memory_size": 8
}


# 4. CREATE MODEL
llm = ChatOllama(
    model=config["model"],
    temperature=config["temperature"]
)


# 5. BUILD SYSTEM MESSAGE
def build_system_message(persona="friendly"):
    """Build the AI instructions using business facts and selected persona."""

    business_facts = f"""
    Business name: {facts['business_name']}
    Business type: {facts['business_type']}
    Location: {facts['location']}
    Platform: {facts['platform']}
    Delivery: {facts['delivery']}
    Prices: {facts['prices']}
    """

    style = personas.get(persona, personas["friendly"])

    return SystemMessage(
        content=f"""
        You are a bakery customer assistant.

        Business information:
        {business_facts}

        Personality:
        {style}

        IMPORTANT RULES:
        - Only use these facts.
        - Never invent prices, products, or business information.
        - If information is missing, politely say you do not know.
        - Never guess.
        """
    )


# 6. CONVERSATION MEMORY
messages = [build_system_message()]

# Store only the user's questions separately.
questions = []


# 7. CHAT LOOP
print("Bot ready. Commands: /persona friendly|formal|sales, /price <item>, /add <item> <price>, bye")

while True:

    user_input = input("You: ").strip()

    if user_input.lower() == "bye":
        print("Bot: Goodbye!")
        print("Questions asked:", len(questions))

        if questions:
            print("First question:", questions[0])
            print("Last question:", questions[-1])

        break

    # PERSONA COMMAND
    elif user_input.lower().startswith("/persona"):

        parts = user_input.split(maxsplit=1)

        if len(parts) == 2:
            persona_name = parts[1].lower()
        else:
            persona_name = "friendly"

        # .get() prevents a wrong persona name from crashing.
        selected_persona = persona_name if persona_name in personas else "friendly"

        messages[0] = build_system_message(selected_persona)

        print("Bot: Style changed to:", personas[selected_persona])

    # PRICE COMMAND
    elif user_input.lower().startswith("/price"):

        parts = user_input.split(maxsplit=1)

        if len(parts) < 2:
            print("Bot: Please enter an item name.")
            continue

        item = parts[1].lower()

        # WHY: Direct dictionary lookup prevents the AI from inventing prices.
        if item in facts["prices"]:
            print(f"Bot: {item.title()} costs {facts['prices'][item]} PKR.")
        else:
            print(f"Bot: Sorry, {item} is not on our menu.")

    # STRETCH: ADD NEW MENU ITEM
    elif user_input.lower().startswith("/add"):

        parts = user_input.split()

        if len(parts) < 3:
            print("Bot: Use /add <item> <price>")
            continue

        item = " ".join(parts[1:-1]).lower()

        try:
            price = int(parts[-1])

            if price <= 0:
                print("Bot: Please enter a price greater than zero.")
                continue

            facts["prices"][item] = price

            # WHY: Rebuilding updates the AI's knowledge immediately.
            current_persona = "friendly"

            for name, description in personas.items():
                if messages[0].content.endswith(description):
                    current_persona = name
                    break

            messages[0] = build_system_message(current_persona)

            print(f"Bot: {item.title()} added for {price} PKR.")

        except ValueError:
            print("Bot: Please enter a valid number for the price.")

    # NORMAL AI CHAT
    else:

        questions.append(user_input)

        messages.append(HumanMessage(content=user_input))

        response = llm.invoke(messages)

        ai_reply = response.content

        print("Bot:", ai_reply)

        messages.append(AIMessage(content=ai_reply))

        # WHY: Keep only recent messages to control memory and token usage.
        memory_limit = config["memory_size"]

        messages = [messages[0]] + messages[-memory_limit:]

