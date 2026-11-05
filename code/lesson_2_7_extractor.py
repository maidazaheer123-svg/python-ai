"""
Lesson 2.7 Order Extractor for Sweet Cravings Diaries.
Extracts WhatsApp-style orders into structured data, validates them against the menu,
calculates totals in Python, and saves approved-by-check orders to JSON and CSV.
Run from the code folder: uv run lesson_2_7_extractor.py
"""
import csv
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from ollama import ResponseError
import httpx

PRICES = {
    "brownie": 270,
    "cupcake": 300,
    "vanilla cake 1 lb": 1400,
    "chocolate cream cake 1 lb": 1600,
    "double chocolate cake 1 lb": 1800,
    "vanilla cake 2 lb": 2000,
    "chocolate cream cake 2 lb": 2200,
    "double chocolate cake 2 lb": 2500,
}
MODEL = "gemma3:1b"
ORDERS_FILE = "orders.json"
CSV_FILE = "orders.csv"

MESSAGES = [
    "Salam! 4 brownies chahiye. I am Sana, address Johar Town.",
    "Hello, I am Ali. Please order 2 cupcakes and 1 vanilla cake 1 lb. Address: Gulberg.",
    "1 pizza and 2 brownies, Bilal, Model Town",
    "Hi, do you deliver to Johar Town?",
    "Assalam o alaikum, main Hira hoon. 3 cupcakes aur 2 brownies chahiye, DHA Lahore.",
]

ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "is_order": {"type": "boolean"},
        "customer": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["item", "quantity"],
            },
        },
    },
    "required": ["is_order", "customer", "address", "items"],
}

extractor = ChatOllama(model=MODEL, temperature=0)


def calculate_total(items: list[dict[str, Any]]) -> int:
    """Calculate order total using only known menu prices."""
    total = 0
    for entry in items:
        item_name = entry.get("item", "")
        quantity = entry.get("quantity", 0)
        # Why: unknown menu items must never be assigned an invented price.
        if item_name in PRICES and isinstance(quantity, int) and quantity > 0:
            total += PRICES[item_name] * quantity
    return total


def extract_message(message: str) -> dict[str, Any] | None:
    """Use the model's JSON-schema output mode to extract an order safely."""
    system_prompt = (
        "Extract customer orders from English and Roman Urdu messages. "
        "Never invent a customer name, address, menu item, or quantity. "
        "Use exact menu names when possible. If the message is not an order, "
        "return is_order=false and an empty items list. Return only schema data."
    )
    try:
        response = extractor.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=message)],
            format=ORDER_SCHEMA,
        )
        # Why: parse explicitly so malformed model output is handled without a traceback.
        return json.loads(response.content)
    except json.JSONDecodeError as exc:
        print(f"CHECK: JSON response could not be parsed: {exc}")
        return None
    except (httpx.ConnectError, ResponseError) as exc:
        print(f"AI service unavailable: {exc}")
        return None


def validate_order(data: dict[str, Any], original_message: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Check extracted keys, customer grounding, menu items, and quantities."""
    checks: list[str] = []
    customer = data.get("customer", None)
    address = data.get("address", None)
    extracted_items = data.get("items", [])
    if not customer:
        checks.append("customer name is missing")
    elif str(customer).lower() not in original_message.lower():
        # Why: the extractor sometimes hallucinates a plausible name absent from the chat.
        checks.append(f"customer {customer!r} is not present in the original message")
    if not isinstance(extracted_items, list) or not extracted_items:
        checks.append("no items were extracted")
        return [], checks

    valid_items: list[dict[str, Any]] = []
    for entry in extracted_items:
        item_name = entry.get("item", "")
        quantity = entry.get("quantity", 0)
        if item_name not in PRICES:
            checks.append(f"{item_name!r} is not on the menu")
            continue
        if not isinstance(quantity, int) or quantity <= 0:
            checks.append(f"quantity for {item_name!r} must be a positive integer")
            continue
        valid_items.append({"item": item_name, "quantity": quantity})
    return valid_items, checks


def write_csv(orders: list[dict[str, Any]]) -> None:
    """Write one CSV row per valid item line, suitable for spreadsheet viewing."""
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["customer", "item", "quantity", "line_total"])
        for order in orders:
            for entry in order.get("items", []):
                name = entry.get("item", "")
                quantity = entry.get("quantity", 0)
                line_total = PRICES.get(name, 0) * quantity
                writer.writerow([order.get("customer", ""), name, quantity, line_total])


def main() -> None:
    """Process the sample messages, print checks and summary, then save valid orders."""
    orders: list[dict[str, Any]] = []
    total_value = 0
    check_count = 0

    for message in MESSAGES:
        print(f"\nMessage: {message}")
        data = extract_message(message)
        if data is None:
            check_count += 1
            print("  CHECK: extraction failed; manual review required")
            continue
        if not data.get("is_order", False):
            print("  Not an order: needs a human reply.")
            continue

        valid_items, checks = validate_order(data, message)
        customer = data.get("customer", None)
        address = data.get("address", None)
        message_total = calculate_total(valid_items)

        for entry in valid_items:
            name = entry.get("item", "")
            quantity = entry.get("quantity", 0)
            print(f"  {quantity} x {name} = {PRICES[name] * quantity} PKR")
        print(f"  Customer: {customer or 'MISSING'}, Address: {address or 'MISSING'}")
        print(f"  Total: {message_total} PKR")
        for warning in checks:
            print(f"  CHECK: {warning}")
        check_count += len(checks)

        # Why: only valid menu items and a grounded customer name are stored.
        if valid_items and customer and str(customer).lower() in message.lower():
            order = {
                "id": f"E{len(orders) + 1:03d}",
                "customer": customer,
                "address": address,
                "items": valid_items,
                "total": message_total,
                "status": "needs_owner_confirmation",
            }
            orders.append(order)
            total_value += message_total

    with open(ORDERS_FILE, "w", encoding="utf-8") as file:
        json.dump(orders, file, indent=2, ensure_ascii=False)
    write_csv(orders)

    print("\n" + "=" * 48)
    print(f"Orders found: {len(orders)} | Total value: {total_value:,} PKR | Checks: {check_count}")
    print(f"Saved {len(orders)} orders to {ORDERS_FILE}")
    print(f"Saved item rows to {CSV_FILE}")


if __name__ == "__main__":
    main()
