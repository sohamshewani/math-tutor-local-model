from mlx_lm import load, generate

print("\n--- Loading Model... ---")
model, tokenizer = load(
    "mlx-community/Qwen2.5-7B-Instruct-4bit",
    adapter_path="adapters"
)
print("--- Model Ready! Type 'exit' to stop ---\n")

while True:
    user_msg = input("\nYou: ")
    if user_msg.strip().lower() in ["exit", "quit", "q"]:
        print("Goodbye!")
        break
    if not user_msg.strip():
        continue
    
    prompt = f"<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n"
    reply = generate(model, tokenizer, prompt=prompt, max_tokens=250)
    print(f"\nAI:\n{reply}\n{'-'*35}")
