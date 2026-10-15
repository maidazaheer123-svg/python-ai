"""This program creates an AI prompt to help a business solve a problem"""
#ask for user input
name = input("your name: ")
business = input("business type: ")
problem = input("biggest problem : ")

print(f"\n welcome {name}")

prompt = f"Suggest 3 AI solutions for a {business} that has the problem of {problem}."

print("---prompt---")
print(prompt)
