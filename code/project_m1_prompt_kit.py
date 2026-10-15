
"""
AI Prompt Kit for a Local Business

This tool asks a business owner five questions and creates
three ready-to-use AI prompts for marketing, customer service,
and business growth.
"""

# Ask for the business details
business_name = input("Business name: ")
business_type = input("Business type: ")
city = input("City: ")
customers = input("Main customers: ")

# Convert the budget from text into an integer
budget = int(input("Monthly budget (PKR): "))

# Display the business name in the heading
print()
print("=" * 40)
print(f"   AI Prompt Kit for {business_name}")
print()
print("=" * 40)

# Prompt 1: Include the business, location, audience, and tone
marketing_prompt = f"""
[1] Marketing

Write a short Instagram post for {business_name},
a {business_type} in {city}.
Target audience: {customers}.
Use a friendly tone and include one call to action.
"""

print(marketing_prompt)
print()
print("-" * 40)


# Prompt 2: Give the AI a role and a clear task
customer_service_prompt = f"""
[2] Customer Service

You are the manager of {business_name}.
Write a polite reply to a customer whose order arrived late.
Apologise sincerely and offer a small discount.
Use a friendly and professional tone.
"""

print(customer_service_prompt)
print()
print("-" * 40)

# Prompt 3: Include a specific number and the client's budget
growth_prompt = f"""
[3] Business Growth

Suggest 3 low-cost AI ideas that a {business_type}
in {city} can use to attract {customers}.
The monthly budget is {budget} PKR.
Give practical suggestions and estimated costs.
Do not invent prices; clearly label estimates and
recommend checking current prices.
"""

print(growth_prompt)
print()
print("-" * 40)

# This prompt saves time by preparing quick customer replies

whatsapp_prompt = f"""
[4] WhatsApp Auto-Reply

You are a friendly customer service assistant for
{business_name}, a {business_type} in {city}.

Write a polite WhatsApp reply to a customer asking
about cake prices and how to place an order.

Keep the reply short and friendly.
Do not invent prices. Ask the customer which cake
they want and what date they need it.
"""

print(whatsapp_prompt)
print()
print("-" * 40)