"""
Task 2.6 - Saved Bot for Sweet Crumbs bakery.

A local chatbot (Ollama) that:
  * reads its facts and prices from faq.json, so the owner can edit them
    without touching the code,
  * remembers the conversation between runs (chat_history.json),
  * never shows a red traceback to a customer: problems become friendly
    messages and are written to errors.log for the developer.

Commands: /reset (forget the chat), /export (write transcript.txt), bye
Setup:    pip install ollama   and have the Ollama app running.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import httpx
import ollama

MODEL = "llama3.2"  # change to whichever model you pulled in Ollama

# Why: paths are built from this file's own folder, so the bot finds its
# files no matter which folder the program is started from.
BASE_DIR = Path(__file__).parent
FAQ_FILE = BASE_DIR / "faq.json"
HISTORY_FILE = BASE_DIR / "chat_history.json"
ERROR_LOG = BASE_DIR / "errors.log"
TRANSCRIPT_FILE = BASE_DIR / "transcript.txt"

MAX_MESSAGES_SENT = 20  # only the latest messages go to the model


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------
def load_faq() -> dict:
    """Load the business facts from faq.json, or exit with a clear message."""
    try:
        with open(FAQ_FILE, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        sys.exit(f"Cannot start: {FAQ_FILE.name} was not found. "
                 "Please put it in the same folder as this program.")
    except json.JSONDecodeError:
        sys.exit(f"Cannot start: {FAQ_FILE.name} is damaged. "
                 "Check it for a missing comma or quote.")


def build_system_message(faq: dict) -> str:
    """Turn the faq dictionary into the instructions the AI always sees."""
    price_lines = ""
    for item, price in faq["prices"].items():
        price_lines += f"- {item}: {price} PKR\n"

    return (
        f"You are the friendly assistant of {faq['business_name']} bakery "
        f"in {faq['city']}. Answer ONLY from the facts below. "
        "If the answer is not there, say you do not know and suggest calling the bakery. "
        "Keep answers short.\n\n"
        f"Opening hours: {faq['opening_hours']}\n"
        f"Delivery: {faq['delivery']}\n"
        f"Custom cakes: {faq['custom_cakes']}\n"
        f"Allergens: {faq['allergens']}\n"
        f"Prices:\n{price_lines}"
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
def load_history() -> list:
    """Load saved messages. A missing or damaged file gives a fresh chat."""
    try:
        with open(HISTORY_FILE, encoding="utf-8") as file:
            history = json.load(file)
    except FileNotFoundError:
        return []  # first run: nothing saved yet, not an error
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("History file was damaged. Starting a fresh chat.")
        return []

    # Why: valid JSON can still have the wrong shape (e.g. someone saved {}),
    # and that would crash later inside ollama.chat().
    is_valid = isinstance(history, list) and all(
        isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
        for m in history
    )
    if not is_valid:
        print("History file was damaged. Starting a fresh chat.")
        return []
    return history


def save_history(history: list) -> None:
    """Write the history to disk in a readable form."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            # ensure_ascii=False keeps Urdu readable instead of \u0622 codes
            json.dump(history, file, indent=2, ensure_ascii=False)
    except OSError as error:
        log_error("save_history", error)
        print("Bot: (I could not save the chat this time.)")


def export_transcript(history: list) -> None:
    """Write the chat as one readable line per message (stretch)."""
    with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as file:
        for message in history:
            file.write(f"{message['role']}: {message['content']}\n")
    print(f"Bot: Chat exported to {TRANSCRIPT_FILE.name}.")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
def log_error(where: str, error: Exception) -> None:
    """Append a timestamped error line to errors.log (never raises)."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as file:
            file.write(f"{stamp} [{where}] {type(error).__name__}: {error}\n")
    except OSError:
        pass  # Why: the error logger must never become the thing that crashes


# ---------------------------------------------------------------------------
# AI call
# ---------------------------------------------------------------------------
def get_reply(system_message: str, history: list) -> str | None:
    """Ask the model for a reply. Returns None (after a friendly message) on failure."""
    # Why: the system message is NOT stored in the history file. It is rebuilt
    # from faq.json on every call, so a price changed in faq.json applies
    # immediately, even in an old conversation.
    messages = [{"role": "system", "content": system_message}]
    messages += history[-MAX_MESSAGES_SENT:]

    try:
        response = ollama.chat(model=MODEL, messages=messages)
        return response["message"]["content"]
    except httpx.ConnectError as error:
        log_error("ollama.chat", error)
        print("Bot: I am offline right now. Please open the Ollama app and try again.")
    except ollama.ResponseError as error:
        log_error("ollama.chat", error)
        print("Bot: Sorry, I could not answer that. Please try again in a moment.")
    except Exception as error:  # last safety net: customers never see a traceback
        log_error("ollama.chat (unexpected)", error)
        print("Bot: Sorry, something went wrong. Please try again.")
    return None


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------
def main() -> None:
    faq = load_faq()
    system_message = build_system_message(faq)
    history = load_history()

    if history:
        print(f"Loaded {len(history)} old messages.")
    print(f"{faq['business_name']} Bot: Ask me anything. Commands: /reset, /export, bye")

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Why: Ctrl+C or Ctrl+D would otherwise end with a red traceback
            print("\nBot: Goodbye! Your chat is saved.")
            break

        if not user_text:
            continue  # Break the Bot: empty input must not be sent to the AI

        if user_text.lower() == "bye":
            print("Bot: Goodbye! Your chat is saved.")
            break
        if user_text.lower() == "/reset":
            history = []
            save_history(history)
            print("Bot: Chat cleared. Starting fresh.")
            continue
        if user_text.lower() == "/export":
            export_transcript(history)
            continue

        history.append({"role": "user", "content": user_text})
        reply = get_reply(system_message, history)

        if reply is None:
            # Why: an unanswered question left in the history would be sent
            # again next turn and break the user/assistant alternation.
            history.pop()
            continue

        print(f"Bot: {reply}")
        history.append({"role": "assistant", "content": reply})
        save_history(history)  # after every turn, so a crash loses nothing


if __name__ == "__main__":
    main()