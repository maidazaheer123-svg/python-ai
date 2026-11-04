"""
Task 2.5 - AI Skills Toolkit for Sweet Crumbs bakery.

One shared toolkit of tested, reusable AI skills (summarize, translate,
reply to reviews) so every staff member gets consistent results instead of
writing their own prompts.

Setup:
    pip install google-generativeai
    set the GOOGLE_API_KEY environment variable (or paste your key below)

Run:
    python lesson_2_5_ai_skills.py
"""

import os

import google.generativeai as genai

# ---------------------------------------------------------------------------
# 1. Models - created ONCE at the top, never inside a function
# ---------------------------------------------------------------------------
# Why: creating a model on every call is slow and wasteful. Build both once
# and let ask_ai() pick between them.
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", "PASTE_YOUR_KEY_HERE"))

MODEL_NAME = "gemini-2.0-flash"  # change if your course uses a different model

precise_model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={"temperature": 0.1},  # low = consistent, factual
)
creative_model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={"temperature": 0.9},  # high = varied, friendly
)

BUSINESS_NAME = "Sweet Crumbs"


# ---------------------------------------------------------------------------
# 2. The one function that talks to the AI
# ---------------------------------------------------------------------------
def ask_ai(prompt: str, system: str = "You are a helpful assistant.",
           creative_mode: bool = False) -> str:
    """Send a prompt to the right model and return the answer as plain text.

    Args:
        prompt: The task or question for the AI.
        system: Instructions about the AI's role and style.
        creative_mode: True uses the high-temperature model.
    """
    # Why: every skill goes through this single door, so model choice, error
    # handling and (later) logging only have to be written in one place.
    model = creative_model if creative_mode else precise_model

    # Why: the model object is shared, so the system text is placed in front
    # of the prompt instead of being baked into the model at creation time.
    full_prompt = f"{system}\n\n{prompt}"
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as error:  # network, quota, blocked content, bad key...
        return f"(AI error: {error})"


# ---------------------------------------------------------------------------
# 3. Skills built on ask_ai() - they RETURN text, the menu PRINTs it
# ---------------------------------------------------------------------------
def summarize(text: str) -> str:
    """Summarize a text in two short sentences."""
    return ask_ai(
        f"Summarize this in two short sentences:\n{text}",
        system=f"You are a precise assistant for {BUSINESS_NAME} bakery.",
    )


def translate(text: str, language: str = "Urdu") -> str:
    """Translate text into a language (default: Urdu). Returns only the translation."""
    return ask_ai(
        f"Translate into {language}. Reply with the translation only:\n{text}",
        system="You are a professional translator.",
    )


def reply_to_review(review: str) -> str:
    """Write a warm, short reply from the bakery to a customer review."""
    return ask_ai(
        f"Write a reply of at most 2 sentences to this customer review:\n{review}",
        system=(f"You are the friendly customer-care voice of {BUSINESS_NAME} bakery. "
                "Thank the customer and apologise for any problem."),
        creative_mode=True,  # warm replies should not sound copy-pasted
    )


# ---------------------------------------------------------------------------
# 4. A helper that needs NO AI (with tests)
# ---------------------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    """Roughly estimate tokens in a text (about 4 characters per token)."""
    return len(text) // 4


# Why: tests for non-AI code are free, instant and always give the same
# answer, so run them at start-up and catch mistakes before using the API.
assert estimate_tokens("") == 0
assert estimate_tokens("abcdefgh") == 2
assert estimate_tokens("Cake was great but delivery was late.") == 9


# ---------------------------------------------------------------------------
# 5. Menu loop + usage counter
# ---------------------------------------------------------------------------
usage = {"summarize": 0, "translate": 0, "reply": 0}

BATCH_REVIEWS = [
    "Best croissants in town!",
    "The cake was dry and the staff seemed rushed.",
    "Loved the birthday cupcakes, but parking was impossible.",
]

print(f"{BUSINESS_NAME} AI Toolkit. Commands: /summarize, /translate, /reply, /batch, bye")

while True:
    command = input("Command: ").strip().lower()

    if command == "bye":
        break

    elif command == "/summarize":
        text = input("Text to summarize: ")
        print("AI:", summarize(text))
        usage["summarize"] += 1

    elif command == "/translate":
        text = input("Text to translate: ")
        language = input("Language (Enter for Urdu): ").strip()
        # Why: only pass language when the user typed one, so pressing Enter
        # really uses the function's default instead of an empty string.
        if language:
            print("AI:", translate(text, language))
        else:
            print("AI:", translate(text))
        usage["translate"] += 1

    elif command == "/reply":
        review = input("Customer review: ")
        print("AI:", reply_to_review(review))
        print(f"    (review was about {estimate_tokens(review)} tokens)")
        usage["reply"] += 1

    elif command == "/batch":
        # Stretch: one skill over a whole list of reviews
        for number, review in enumerate(BATCH_REVIEWS, start=1):
            print(f"{number}. {review}")
            print(f"   AI: {reply_to_review(review)}")
            usage["reply"] += 1

    else:
        print("Unknown command. Try /summarize, /translate, /reply, /batch or bye.")

print("Skills used today:")
for skill, count in usage.items():
    print(f"  {skill}: {count}")