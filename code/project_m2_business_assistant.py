"""
Sweet Cravings Diaries AI Business Assistant.
Reads owner-editable bakery facts, answers using tools, and saves approved orders.
Run from the code folder: uv run project_m2_business_assistant.py
"""
import json
import os
import re
from typing import Any
from uuid import uuid4

import httpx
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from pydantic import ValidationError
from ollama import ResponseError

BUSINESS_FILE = "business.json"
ORDERS_FILE = "orders.json"
TRANSCRIPT_FILE = "transcript.json"
ERROR_FILE = "errors.log"
MODEL = "gemma3:1b"
EXTRACTOR_MODEL = "gemma3:1b"
MAX_STEPS = 5
MAX_MEMORY_MESSAGES = 8

TOOL_COUNTS = {"get_price": 0, "get_info": 0, "order_status": 0, "place_order": 0}
questions = answered = errors = whatsapp_imports = orders_placed = 0


def load_json(path: str, default: Any) -> Any:
    """Load JSON; use a safe default if a record file is missing or damaged."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, OSError) as exc:
        if path == BUSINESS_FILE:
            raise
        print(f"Warning: {path} is missing or damaged; starting fresh.")
        log_error(f"{path}: {exc}")
        return default


def save_json(path: str, data: Any) -> None:
    """Save JSON in readable, Unicode-preserving format."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def log_error(message: str) -> None:
    """Append technical details to a private log, not to customer-facing output."""
    with open(ERROR_FILE, "a", encoding="utf-8") as file:
        file.write(message + "\n")


def calculate_total(items: list[dict[str, Any]], prices: dict[str, int]) -> int:
    """Calculate order total in Python and reject unknown items or invalid quantities."""
    total = 0
    for item in items:
        name = item.get("item")
        quantity = item.get("quantity")
        assert isinstance(quantity, int) and quantity > 0, "quantity must be positive"
        if name not in prices:
            raise ValueError(f"{name!r} is not on the menu")
        total += prices[name] * quantity
    return total


def next_order_id(orders: list[dict[str, Any]]) -> str:
    """Create a readable unique order identifier."""
    existing = {order.get("id") for order in orders}
    number = len(orders) + 101
    while f"A{number}" in existing:
        number += 1
    return f"A{number}"


def load_business() -> dict[str, Any]:
    """Load business facts, with a clear instruction if the owner file is absent."""
    try:
        data = load_json(BUSINESS_FILE, None)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Could not read {BUSINESS_FILE}: {exc}. Please repair or create it.")
        raise SystemExit(1)
    if data is None:
        print(f"Missing {BUSINESS_FILE}. Please create it before running the assistant.")
        raise SystemExit(1)
    if not isinstance(data.get("prices"), dict):
        print("business.json must contain a prices dictionary.")
        raise SystemExit(1)
    return data


business = load_business()
prices: dict[str, int] = business["prices"]
orders: list[dict[str, Any]] = load_json(ORDERS_FILE, [])
transcript: list[dict[str, str]] = load_json(TRANSCRIPT_FILE, [])
llm = ChatOllama(model=MODEL, temperature=0)
extractor = ChatOllama(model=EXTRACTOR_MODEL, temperature=0)


@tool(parse_docstring=True)
def get_price(item: str) -> str:
    """Read the exact price for a menu item.

    Args:
        item: Exact menu item name.
    """
    if item not in prices:
        return f"{item} is not on the menu. I cannot quote a price."
    return f"{item} costs {prices[item]} {business.get('currency', 'PKR')}"


@tool(parse_docstring=True)
def get_info(topic: str) -> str:
    """Read business information from the owner data file.

    Args:
        topic: Business information key such as hours, delivery, name, or city.
    """
    value = business.get(topic.lower())
    if value is None:
        return f"I don't have confirmed information about {topic}. Please ask the owner."
    return f"{topic}: {value}"


@tool(parse_docstring=True)
def order_status(order_id: str) -> str:
    """Check an order's status in the saved order file.

    Args:
        order_id: Order identifier such as A101.
    """
    for order in orders:
        if order.get("id", "").lower() == order_id.lower():
            return f"Order {order_id} for {order.get('customer')} is {order.get('status')}, total {order.get('total')} PKR"
    return f"Order {order_id} was not found."


@tool(parse_docstring=True)
def place_order(item: str, quantity: int, customer: str) -> str:
    """Request approval and place an order using a Python-calculated total.

    Args:
        item: Exact menu item name.
        quantity: Number of units requested.
        customer: Customer name provided in the conversation.
    """
    if item not in prices:
        return f"Cannot place order: {item} is not on the menu."
    if quantity <= 0 or not customer.strip():
        return "Cannot place order: quantity and customer name must be valid."
    total = calculate_total([{"item": item, "quantity": quantity}], prices)
    approval = input(f"  [approve] {quantity} x {item} for {customer} = {total} PKR. Place it? (yes/no) ").strip().lower()
    if approval != "yes":
        return "Owner declined. No order saved."
    order = {"id": next_order_id(orders), "customer": customer, "items": [{"item": item, "quantity": quantity}],
             "total": total, "status": "received"}
    orders.append(order)
    save_json(ORDERS_FILE, orders)
    global orders_placed
    orders_placed += 1
    return f"Order {order['id']} placed: {quantity} x {item}, total {total} PKR"


TOOLS = {tool_obj.name: tool_obj for tool_obj in [get_price, get_info, order_status, place_order]}
model_with_tools = llm.bind_tools(list(TOOLS.values()))
SYSTEM_PROMPT = (
    f"You are the friendly assistant for {business['name']}. Answer using owner facts and tools. "
    "Never guess prices, hours, delivery terms, or order statuses. For prices, call get_price. "
    "For business details, call get_info. Check statuses with order_status. Orders must always use place_order "
    "and its owner approval. Do not promise availability or delivery."
)


def save_transcript() -> None:
    """Persist conversation messages as plain role/content dictionaries."""
    save_json(TRANSCRIPT_FILE, transcript)


def run_agent(user_text: str) -> str:
    """Run a bounded tool-calling loop; every tool result is linked by tool_call_id."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for entry in transcript[-MAX_MEMORY_MESSAGES:]:
        if entry["role"] == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry["role"] == "assistant":
            messages.append(AIMessage(content=entry["content"]))
    messages.append(HumanMessage(content=user_text))
    for step in range(MAX_STEPS):
        response = model_with_tools.invoke(messages)
        calls = getattr(response, "tool_calls", [])
        if not calls:
            return str(response.content)
        messages.append(response)
        for call in calls:
            name = call.get("name", "")
            args = call.get("args", {})
            call_id = call.get("id", str(uuid4()))
            print(f"  [tool] {name}({args}) -> ", end="")
            if name not in TOOLS:
                result = f"Unknown tool: {name}"
            else:
                try:
                    TOOL_COUNTS[name] += 1
                    result = TOOLS[name].invoke(args)
                except ValidationError as exc:
                    result = f"Invalid tool arguments: {exc}"
                except (ValueError, TypeError) as exc:
                    result = f"Could not complete tool: {exc}"
            print(result)
            messages.append(ToolMessage(content=str(result), tool_call_id=call_id))
    # The for-else fallback prevents an agent from looping forever.
    else:
        return "I reached the maximum tool steps. Please ask a simpler question or contact the owner."
    return "I couldn't complete that request."


ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "is_order": {"type": "boolean"},
        "customer": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]},
        "items": {"type": "array", "items": {"type": "object", "properties": {
            "item": {"type": "string"}, "quantity": {"type": "integer"}
        }, "required": ["item", "quantity"]}}
    },
    "required": ["is_order", "customer", "address", "items"]
}


def import_whatsapp() -> None:
    """Extract WhatsApp order fields, run checks, calculate total, and request approval."""
    global whatsapp_imports, orders_placed
    whatsapp_imports += 1
    raw = input("Paste the WhatsApp message: ").strip()
    if not raw:
        print("No message provided.")
        return
    prompt = ("Extract an order from the message. Do not invent customer names or menu items. "
              "If it is not an order, is_order=false. Return only schema-compliant data.\nMESSAGE:\n" + raw)
    try:
        response = extractor.invoke([SystemMessage(content="You extract structured order information."),
                                     HumanMessage(content=prompt)], format=ORDER_SCHEMA)
        parsed = json.loads(response.content) if isinstance(response.content, str) else response.content
    except (httpx.ConnectError, ResponseError) as exc:
        log_error(f"WhatsApp extractor: {type(exc).__name__}: {exc}")
        print("The AI service is offline or unavailable. Please try later.")
        return
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        log_error(f"WhatsApp extraction invalid: {exc}")
        print("I couldn't safely read that message. Please check it manually.")
        return
    if not parsed.get("is_order"):
        print("Not an order: this message needs a human reply.")
        return
    checks: list[str] = []
    customer = parsed.get("customer")
    if not customer:
        checks.append("customer name is missing")
    elif customer.lower() not in raw.lower():
        checks.append(f"customer {customer!r} is not in the message (possibly invented)")
    items = parsed.get("items", [])
    if not items:
        checks.append("no order items were extracted")
    for entry in items:
        name, quantity = entry.get("item"), entry.get("quantity")
        if name not in prices:
            checks.append(f"{name!r} is not on the menu")
        if not isinstance(quantity, int) or quantity <= 0:
            checks.append(f"invalid quantity for {name!r}")
    try:
        # Calculate only known menu items with valid quantities; never price an unknown item.
        valid_items = [entry for entry in items if entry.get("item") in prices and
                       isinstance(entry.get("quantity"), int) and entry["quantity"] > 0]
        total = calculate_total(valid_items, prices)
    except (ValueError, AssertionError) as exc:
        checks.append(str(exc))
        total = 0
    for entry in valid_items:
        print(f"  {entry['quantity']} x {entry['item']} = {prices[entry['item']] * entry['quantity']} PKR")
    print(f"  Customer: {customer or 'MISSING'}, Address: {parsed.get('address') or 'MISSING'}")
    print(f"  Python total for valid menu items: {total} PKR")
    for problem in checks:
        print(f"  CHECK: {problem}")
    approval = input("  [approve] Save this order? (yes/no) ").strip().lower()
    if approval == "yes" and not checks:
        order = {"id": next_order_id(orders), "customer": customer,
                 "items": items, "total": total, "status": "received", "address": parsed.get("address")}
        orders.append(order)
        save_json(ORDERS_FILE, orders)
        orders_placed += 1
        print(f"Saved order {order['id']}.")
    else:
        print("Not saved. Resolve checks and obtain owner approval first.")


def show_orders() -> None:
    """Print orders in a numbered list."""
    if not orders:
        print("No orders on file.")
        return
    for index, order in enumerate(orders, start=1):
        print(f"  {index}. {order.get('id')} | {order.get('customer')} | {order.get('total')} PKR | {order.get('status')}")


def main() -> None:
    """Run command loop and print a useful session report at exit."""
    global questions, answered, errors
    print("=" * 60)
    print(f"   {business['name']} AI Business Assistant")
    print("=" * 60)
    print("Ask anything, or use: /import, /orders, /reset, bye")
    while True:
        user_text = input("You: ").strip()
        if not user_text:
            print("Please enter a question or command.")
            continue
        if user_text.lower() == "bye":
            print("Assistant: Goodbye! Everything is saved.")
            break
        if user_text == "/orders":
            show_orders()
            continue
        if user_text == "/import":
            import_whatsapp()
            continue
        if user_text == "/reset":
            transcript.clear()
            save_transcript()
            print("Chat cleared. Saved orders are kept.")
            continue
        questions += 1
        transcript.append({"role": "user", "content": user_text})
        try:
            reply = run_agent(user_text)
            print(f"Assistant: {reply}")
            transcript.append({"role": "assistant", "content": reply})
            answered += 1
        except (httpx.ConnectError, ResponseError) as exc:
            errors += 1
            log_error(f"{type(exc).__name__}: {exc}")
            print("The AI service is unavailable right now. Please try again later.")
            transcript.append({"role": "assistant", "content": "Service unavailable."})
        except Exception as exc:
            errors += 1
            log_error(f"Unexpected {type(exc).__name__}: {exc}")
            print("Something went wrong. Please try again or contact the owner.")
            transcript.append({"role": "assistant", "content": "Request could not be completed."})
        save_transcript()
    print("=" * 60)
    print("Session report")
    print(f"Questions: {questions} | Answered: {answered} | Errors: {errors}")
    print(f"WhatsApp imports: {whatsapp_imports} | Orders placed: {orders_placed} | Orders on file: {len(orders)}")
    print("Tool calls:")
    for name, count in TOOL_COUNTS.items():
        print(f"  {name}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
