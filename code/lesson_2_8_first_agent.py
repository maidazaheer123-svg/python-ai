"""Task 2.8 - Sweet Crumbs Agent

An assistant for the Sweet Crumbs bakery that does things, not just talks.
It has four tools:
  - get_price     (READ)   looks up the price of a menu item
  - order_status  (CHECK)  checks where an existing order is
  - place_order   (ACT)    places a new order, but ONLY after the owner types "yes"
  - search_faq    (READ)   answers questions from faq.json (Task 2.6, stretch)

How it works: the model decides which tool to call, our loop runs it, and the
result goes back to the model, until the model answers in plain text or we hit
MAX_STEPS. The whole conversation lives in `messages`, so the agent remembers
earlier questions. Type 'bye' to exit.

Setup:
    pip install langchain-openai langchain-core
    export OPENAI_API_KEY=...        (or swap make_llm() for your provider)

----------------------------------------------------------------------------
WATCH THE AGENT THINK - RESULTS (Lesson 2.8, Section 7)
Run each prompt, then fill in what the agent actually did.

| # | Prompt                                   | Right tool(s)            | Picked right? |
|---|------------------------------------------|--------------------------|---------------|
| 1 | Compare the price of a brownie and cake  | get_price x2             |               |
| 2 | Where is my order A102?                  | order_status             |               |
| 3 | I am Ali, I want 2 brownies              | place_order (+ approval) |               |
| 4 | Do you deliver on Sundays? (FAQ)         | search_faq               |               |
| 5 | Tell me a joke                           | no tool                  |               |
| 6 | Where is order Z999?                     | order_status (not found) |               |

Right tool picked: ___ / 6
----------------------------------------------------------------------------
"""

import json
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import ValidationError

# ----------------------------------------------------------------------------
# The owner's data (in a real shop this would come from a database)
# ----------------------------------------------------------------------------
PRICES = {"brownie": 300, "cupcake": 250, "cookie": 120, "cake": 2500}
ORDERS = {
    "A101": "Order A101 was delivered",
    "A102": "Order A102 is out for delivery",
    "A103": "Order A103 is being baked",
}
FAQ_FILE = Path("faq.json")  # from Task 2.6

MAX_STEPS = 5  # why: a confused model could call tools forever; this caps cost and time


# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------
@tool(parse_docstring=True)
def get_price(item: str) -> str:
    """Look up the price of one menu item in PKR.

    Args:
        item: Name of the menu item, for example brownie, cupcake, cookie or cake.
    """
    key = item.strip().lower()
    if key not in PRICES:
        return f"Sorry, {item} is not on the menu. Menu: {', '.join(PRICES)}"
    return f"{key} costs {PRICES[key]} PKR"


@tool(parse_docstring=True)
def order_status(order_id: str) -> str:
    """Check the current status of an existing order.

    Args:
        order_id: The order number, for example A102.
    """
    return ORDERS.get(order_id.strip().upper(), f"Order {order_id} was not found")


@tool(parse_docstring=True)
def place_order(item: str, quantity: int, customer: str) -> str:
    """Place a new order for a customer. The owner must approve it first.

    Args:
        item: Name of the menu item to order, for example brownie.
        quantity: How many pieces to order. Must be at least 1.
        customer: The customer's name.
    """
    key = item.strip().lower()
    if key not in PRICES:
        return f"Order not placed: {item} is not on the menu"
    if quantity < 1:
        return "Order not placed: quantity must be at least 1"

    total = PRICES[key] * quantity

    # why: this tool spends the owner's money and can't be undone, so the human
    # decides here in code. The model can't skip or talk its way past input().
    answer = input(f"  [approve] {quantity} x {key} for {customer} = {total} PKR. Place it? (yes/no) ")
    if answer.strip().lower() not in ("yes", "y"):
        return "Order NOT placed: the owner said no"

    order_id = f"A{101 + len(ORDERS)}"
    ORDERS[order_id] = f"Order {order_id} is being baked"
    return f"Order {order_id} placed: {quantity} x {key}, total {total} PKR"


@tool(parse_docstring=True)
def search_faq(question: str) -> str:
    """Find an answer to a common question in the owner's FAQ file.

    Args:
        question: The customer's question or a few keywords, for example "delivery on Sunday".
    """
    if not FAQ_FILE.exists():
        return "The FAQ file (faq.json) was not found"
    data = json.loads(FAQ_FILE.read_text(encoding="utf-8"))

    # Accept {"question": "answer"} or [{"question": ..., "answer": ...}, ...]
    if isinstance(data, dict):
        entries = list(data.items())
    else:
        entries = [(e.get("question", ""), e.get("answer", "")) for e in data]

    words = {w for w in question.lower().split() if len(w) > 2}
    best, best_score = None, 0
    for q, a in entries:
        score = len(words & set(q.lower().split()))
        if score > best_score:
            best, best_score = (q, a), score
    return f"{best[0]} -> {best[1]}" if best else "No matching FAQ entry found"


# why: a dict lets us find the right function by name in one step, and lets us
# detect a tool name the model invented instead of crashing on a missing function.
TOOLS = {t.name: t for t in (get_price, order_status, place_order, search_faq)}


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------
def make_llm():
    """Create the chat model. Swap this for your own provider if needed."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


SYSTEM_PROMPT = (
    "You are the Sweet Crumbs bakery assistant. Prices are in PKR. "
    "Never guess prices, order status or shop policies: use the tools. "
    "For a price comparison, call get_price once per item. "
    "To place an order you need the item, quantity and the customer's name; "
    "ask if one is missing. Do not ask for approval yourself, the place_order "
    "tool asks the owner. Keep answers short and friendly."
)


# ----------------------------------------------------------------------------
# Running one tool call safely
# ----------------------------------------------------------------------------
def run_tool(call: dict) -> str:
    """Run one tool call from the model and always return a string."""
    name, args = call["name"], call["args"]
    tool_fn = TOOLS.get(name)
    if tool_fn is None:
        # Unknown tool name: tell the model what exists so it can recover.
        return f"Error: unknown tool '{name}'. Available tools: {', '.join(TOOLS)}"
    try:
        return str(tool_fn.invoke(args))
    except ValidationError as err:
        # Wrong or missing arguments (e.g. quantity="two"). Report, don't crash.
        return f"Error: wrong arguments for {name}: {err.errors()[0]['msg']}"
    except Exception as err:  # any other tool failure should not kill the chat
        return f"Error: {name} failed: {err}"


# ----------------------------------------------------------------------------
# The agent loop
# ----------------------------------------------------------------------------
def run_agent(llm_with_tools, messages: list) -> str:
    """Let the model call tools until it gives a final answer (max MAX_STEPS)."""
    for _ in range(MAX_STEPS):
        ai_message = llm_with_tools.invoke(messages)
        messages.append(ai_message)

        if not ai_message.tool_calls:  # no tool needed: this is the final answer
            reply = ai_message.content
            break

        for call in ai_message.tool_calls:
            result = run_tool(call)
            print(f"  [tool] {call['name']}({call['args']}) -> {result}")
            # why: tool_call_id links this result to the exact request, so the
            # model knows which answer belongs to which call (needed for two
            # get_price calls in one turn).
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
    else:
        # Loop ran out of steps without a final answer.
        reply = "Sorry, I could not finish that. Could you rephrase or ask it in smaller parts?"
        messages.append(AIMessage(content=reply))  # keep history valid for the next turn

    return reply


# ----------------------------------------------------------------------------
# Chat loop with memory
# ----------------------------------------------------------------------------
def main() -> None:
    llm_with_tools = make_llm().bind_tools(list(TOOLS.values()))

    # why: `messages` is the agent's memory. We never reset it between questions,
    # so "make it 3 instead" still makes sense after an earlier order.
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    print("Sweet Crumbs Agent: ask about prices, orders, or place an order. Type 'bye' to exit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "bye":
            break
        if not user_input:
            continue

        messages.append(HumanMessage(content=user_input))
        print(f"Agent: {run_agent(llm_with_tools, messages)}")


if __name__ == "__main__":
    main()