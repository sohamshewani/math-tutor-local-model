from openai import OpenAI

# Connect directly to your local MLX server
client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="empty"  # Local server does not need an API key
)

print("Sending request to local fine-tuned model...")

response = client.chat.completions.create(
    model="default_model",
    messages=[
        {"role": "system", "content": "You are an expert assistant and coder. Always provide complete, working code."},
        {"role": "user", "content": "Write a complete Python Tkinter script for a digital clock."}
    ],
    max_tokens=600
)

print("\n--- AI Response ---\n")
print(response.choices[0].message.content)
