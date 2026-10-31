
"""
Task 2.4: Batch Product Writer

This program generates descriptions for all bakery products
using AI, skips products without prices, and calculates
total tokens and execution time.
"""

import time
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# Store bakery products and their prices.
products = {
    "Vanilla Cake": 1400,
    "Chocolate Cream Cake": 1600,
    "Double Chocolate Cake": 1800,
    "Brownie": 270,
    "Cupcakes": 300,
    "Old Stock": 0
}

# Why: Create the model once to avoid creating it again for every product.
model = ChatOllama(model="gemma3:1b")

# Store generated descriptions.
results = []

# Why: Start counters before the loop to calculate total usage.
total_tokens = 0
total_seconds = 0

# Process every product and its price.
for name, price in products.items():

    # Skip products that have no price.
    if price == 0:
        print(f"Skipping {name} (no price)")
        continue

    # Why: Start the timer separately for each AI request.
    start_time = time.time()

    prompt = f"""
    Write one short, attractive sentence describing
    this bakery product: {name}.
    """

    response = model.invoke([HumanMessage(content=prompt)])

    end_time = time.time()

    # Get AI-generated description.
    description = response.content

    # Get token usage.
    usage = response.usage_metadata
    tokens = usage["total_tokens"]

    # Calculate time taken for this request.
    seconds = end_time - start_time

    # Add tokens and seconds to total counters.
    total_tokens += tokens
    total_seconds += seconds

    # Save product information in a dictionary.
    results.append({
        "item": name,
        "price": price,
        "text": description
    })

# Print the final menu.
print("=" * 50)

for number, product in enumerate(results, start=1):
    print(f"{number}. {product['item']} ({product['price']} PKR)")
    print(f"   {product['text']}")

print("=" * 50)

# Print final summary.
print(
    f"{len(results)} descriptions, "
    f"{total_tokens} tokens, "
    f"{total_seconds:.1f} seconds"
)
