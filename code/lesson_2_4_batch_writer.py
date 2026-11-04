"""
Task 2.4: Batch Product Writer

The owner has a price list but no menu descriptions. This script writes
a one-sentence description for every priced item in one run, then prints
a numbered menu and reports the total tokens and seconds used.

Why? Writing descriptions by hand takes a whole day. A loop does it in
under a minute and shows exactly what it cost.
"""

import time

from langchain_ollama import ChatOllama

# Why create the model once, outside the loop? Building it takes time
# and memory, so doing it for every product would be slow and wasteful.
llm = ChatOllama(
    model="gemma3:1b",
    temperature=0.7
)

# Price list for a Lahore bakery (prices in PKR). Old stock has price 0.
products = {
    "Chocolate Cake": 1500,
    "Cupcake": 250,
    "Brownie": 300,
    "Donut": 200,
    "Cheesecake Slice": 450,
    "Old stock": 0,
}

# Results: a list of dictionaries (item, price, text)
results = []

# Why start accumulators at 0 before the loop? They add up a little on
# every pass, so they need a known starting value to build on.
total_tokens = 0
total_seconds = 0.0

for name, price in products.items():

    # Why skip price 0? These items are not for sale, so calling the AI
    # would waste time and tokens on a description nobody will read.
    if price == 0:
        print(f"Skipping {name} (no price)")
        continue

    prompt = (
        f"Write one short, tasty sentence describing '{name}' "
        f"for a bakery menu in Lahore. Reply with the sentence only."
    )

    start = time.time()
    response = llm.invoke(prompt)
    elapsed = time.time() - start

    # Add this call's cost to the running totals
    total_seconds += elapsed
    total_tokens += response.usage_metadata["total_tokens"]

    # Save this item as a dictionary
    results.append({
        "item": name,
        "price": price,
        "text": response.content.strip(),
    })

# Numbered menu
print("=" * 50)
for number, entry in enumerate(results, start=1):
    print(f"{number}. {entry['item']} ({entry['price']} PKR)")
    print(f"   {entry['text']}")
print("=" * 50)

# Summary line
print(f"{len(results)} descriptions, {total_tokens} tokens, {total_seconds:.1f} seconds")