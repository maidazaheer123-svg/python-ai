"""AI Content Studio for Sweet Crumbs, a bakery in Lahore.

The studio writes a description for every menu item in one batch, streams
social media posts in the tone the owner picks, answers prices straight from
data (no AI), and chats with customers using memory and only real facts.
It ends with a session report of what the AI did and what it used.
"""

from langchain.chat_models import init_chat_model

# ---------- A. Setup and data ----------
config = {
    "model": "ollama:llama3.2",  # change to the model you use in class
    "max_messages": 6,           # how many chat messages we keep besides the system message
}

facts = {
    "name": "Sweet Crumbs",
    "city": "Lahore",
    "hours": "9 am to 10 pm, every day",
    "delivery": "200 PKR, free for orders from 3,000 PKR",
    "payment": "cash or bank transfer",
    "prices": {
        "chocolate cake": 1500,
        "cupcake": 250,
        "brownie": 300,
        "mango tart": 0,  # 0 means coming soon
    },
}

tones = {
    "fun": "playful and full of energy, short sentences",
    "premium": "elegant and calm, focused on quality",
    "urgent": "exciting and time-limited, makes people act today",
}
default_tone = "fun"

# Two models, created once: low temperature for facts, high for marketing text.
precise = init_chat_model(config["model"], temperature=0.2)
creative = init_chat_model(config["model"], temperature=0.8)

# Build the price lines first so the system message can use them.
price_lines = ""
for item, price in facts["prices"].items():
    if price == 0:
        price_lines += f"- {item}: coming soon\n"
    else:
        price_lines += f"- {item}: {price:,} PKR\n"

system_text = f"""You are the friendly assistant of {facts['name']}, a bakery in {facts['city']}.
Opening hours: {facts['hours']}.
Delivery: {facts['delivery']}.
Payment: {facts['payment']}.
Menu:
{price_lines}
Only use these facts. If the answer is not in them, say you do not know
and that you can only help with our bakery. Never invent prices or products."""

messages = [{"role": "system", "content": system_text}]

# Accumulators for the session report
total_tokens = 0
total_seconds = 0.0
chat_answers = 0
menu_descriptions = 0
posts = 0
price_answers = 0

# ---------- B. The command loop ----------
print("=" * 50)
print(f"   {facts['name']} AI Content Studio")
print("=" * 50)
print("Commands: /menu, /post fun|premium|urgent, /price <item>, /reset, bye")

while True:
    user_text = input("You: ").strip()
    lowered = user_text.lower()  # lowercase copy so commands work with any capitals

    if user_text == "":
        continue

    if lowered == "bye":
        print("Studio: Goodbye!")
        break

    elif lowered == "/menu":
        # ---------- C. Batch descriptions ----------
        menu = []
        for item, price in facts["prices"].items():
            # Skip BEFORE calling the AI: a coming-soon item must cost nothing.
            if price == 0:
                print(f"Studio: Skipping {item} (coming soon)")
                continue
            response = creative.invoke(
                f"Write ONE short, appetizing sentence describing {item} "
                f"from {facts['name']}, a bakery in {facts['city']}. No price."
            )
            menu.append({"name": item.title(), "price": price, "description": response.text.strip()})
            total_tokens += response.usage_metadata["total_tokens"]
            total_seconds += response.response_metadata.get("total_duration", 0) / 1e9
            menu_descriptions += 1

        print("-" * 50)
        for number, entry in enumerate(menu, start=1):
            print(f"{number}. {entry['name']} ({entry['price']:,} PKR)")
            print(f"   {entry['description']}")
        print("-" * 50)

    elif lowered.startswith("/post"):
        # ---------- D. Streamed post ----------
        tone_name = lowered[len("/post"):].strip()
        # .get() with a default so an unknown tone like "pirate" never raises KeyError
        tone_description = tones.get(tone_name, tones[default_tone])
        post_prompt = (
            f"Write a short Instagram post for {facts['name']} in {facts['city']}. "
            f"Tone: {tone_description}. Use only these facts: hours {facts['hours']}, "
            f"menu:\n{price_lines}Mention one item with its price."
        )
        print(f"Studio ({tone_description}):")
        for chunk in creative.stream(post_prompt):
            print(chunk.text, end="", flush=True)
            # Token and time numbers usually arrive on the last chunk only
            if chunk.usage_metadata:
                total_tokens += chunk.usage_metadata["total_tokens"]
                total_seconds += chunk.response_metadata.get("total_duration", 0) / 1e9
        print()
        posts += 1

    elif lowered.startswith("/price"):
        # ---------- E. Price answers: plain dictionary, no AI call ----------
        wanted = lowered[len("/price"):].strip()
        price = facts["prices"].get(wanted, None)
        if price is None:
            print("Studio: Sorry, that is not on our menu.")
        elif price == 0:
            print(f"Studio: {wanted.title()} is coming soon.")
        else:
            print(f"Studio: {wanted.title()} costs {price:,} PKR.")
        price_answers += 1

    elif lowered == "/reset":
        messages = [messages[0]]  # keep the system message, drop the rest
        print("Studio: Chat cleared.")

    else:
        # Chat with memory, using the precise model so facts stay accurate
        messages.append({"role": "user", "content": user_text})
        # Trim old turns but always keep the system message, or the facts rules are lost
        messages = [messages[0]] + messages[1:][-config["max_messages"]:]

        response = precise.invoke(messages)
        messages.append({"role": "assistant", "content": response.text})

        total_tokens += response.usage_metadata["total_tokens"]
        total_seconds += response.response_metadata.get("total_duration", 0) / 1e9
        chat_answers += 1

        print(f"Studio: {response.text.strip()}")
        print(f"        (memory: {len(messages)} messages, "
              f"{response.usage_metadata['input_tokens']} tokens sent)")

# ---------- F. Session report ----------
print("=" * 50)
print("Session report")
print(f"Chat answers: {chat_answers} | Menu descriptions: {menu_descriptions} | "
      f"Posts: {posts} | Price answers: {price_answers}")
print(f"AI usage: {total_tokens:,} tokens in {total_seconds:.1f} seconds")
print("=" * 50)