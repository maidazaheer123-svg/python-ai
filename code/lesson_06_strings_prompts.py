"""
This program cleans the user's name and question,
counts characters, estimates tokens, and builds a prompt.
"""

name = input("Your name: ")
question = input("Your question: ")

# Why: strip() removes extra spaces and title() capitalizes the name.
name = name.strip().title()
question = question.strip().capitalize()

characters = len(question)
tokens = round(characters / 4)

# Why: lower() makes the check work for Python, PYTHON, or python.
mentions_python = "python" in question.lower()

# Why: This replaces an unwanted word before adding the question to the prompt.
question = question.replace("stupid", "***")


prompt = f"""You are a friendly Python tutor.
Greet {name} by name and answer in 3 short lines.
Question: {question[:150]}"""

print("=" * 40)
print(f"Cleaned question: {question}")
print(f"Characters: {characters}, about {tokens} tokens")
print(f"Mentions Python: {mentions_python}")
print("=" * 40)
print(prompt)

# Why: This estimates the cost using the example price per 1,000 tokens.
price = 0.50
cost = tokens / 1000 * price
print(f"Estimated cost: {cost:.2f} PKR")
