# Lesson 2.7 — Hallucination Hunt

**Project:** Sweet Cravings Diaries Order Extractor  
**Model configured:** `gemma3:1b` (Ollama), temperature `0`  
**Status:** Test plan prepared; live model outputs must be recorded after running locally.

## What the extractor is being checked for

| Hallucination risk | Test message | Code check | Expected result |
|---|---|---|---|
| Invented customer | “2 brownies for delivery to Gulberg” (no customer name) | Customer `.get()` value is required | `CHECK: customer name is missing`; order is not saved |
| Customer name invented by model | Message says “2 cupcakes, address DHA” but model returns “Ali” | Name must occur in the original message | `CHECK: customer 'Ali' is not present...`; order not saved |
| Off-menu product | “1 pizza and 2 brownies, Bilal, Model Town” | Item must be a key in `PRICES` | `CHECK: 'pizza' is not on the menu`; pizza never priced |
| Unsupported quantity | A model response contains quantity 0 or a non-integer | Quantity must be a positive integer | CHECK warning; invalid item omitted |
| Non-order interpreted as order | “hi do you deliver to Johar Town?” | Schema includes `is_order`; false means human response | Printed as “Not an order: needs a human reply.” |
| JSON response malformed | Extractor output cannot be parsed | `json.loads` inside `try/except json.JSONDecodeError` | CHECK; message is not stored |

## Example findings to record after running

For the pizza message, the desired safe behavior is to show the valid brownie line (2 × brownie = 540 PKR using the Sweet Cravings Diaries price list), flag pizza as off-menu, and not store the extracted order unless the customer name is grounded in the original message.

For an ordinary order with a real customer name included in the message, the extractor should print each recognized item, calculate the total in Python, and save it to `orders.json`. The CSV stretch writes one row per recognized item to `orders.csv`.

## Local run record

- Date tested: **Fill in after execution**
- Ollama/model available: **Confirm locally**
- Actual AI extraction: **Not yet recorded**
- Mistake or near miss observed: **Record actual model output**
- What the code caught: **Record actual CHECK messages**
- Additional change made: Customer grounding, menu validation, positive quantity validation, Python-only totals, and parse-error handling are implemented.

**Honesty note:** This document describes the planned hunt and implemented safeguards. It does not claim that an Ollama run has been performed or that any specific hallucination was observed. Update the run record with genuine terminal results before submission.
