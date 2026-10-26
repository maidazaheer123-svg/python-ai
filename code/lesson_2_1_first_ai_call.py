
"""AI tutor that explains topics at the student's level."""

import time
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

topic = input("Topic: ").strip()
level = input("Level (beginner or expert): ").strip()

# Why: A low temperature helps produce more consistent answers.
model = init_chat_model("ollama:gemma3:1b", temperature=0.2)

# Why: The student's level determines how the topic is explained.
system_message = SystemMessage(
    content=(
        f"You are a helpful tutor teaching at {level} level. "
        "Keep your answer short, around 3 sentences. "
        "For beginners, use simple words and examples. "
        "For experts, include technical details."
    )
)

human_message = HumanMessage(content=topic)

start_time = time.time()
response = model.invoke([system_message, human_message])
end_time = time.time()

print("=" * 40)
print(response.text)
print("=" * 40)

usage = response.usage_metadata
total_tokens = usage["total_tokens"]
total_duration = end_time - start_time

print(f"{total_tokens} tokens in {total_duration:.1f} seconds")
