from mlx_lm import load, generate

print("\n--- Loading Fine-Tuned Model... ---")
model, tokenizer = load(
    "mlx-community/Qwen2.5-7B-Instruct-4bit",
    adapter_path="adapters"
)
print("--- Model Ready! Type 'exit' to quit | Type 'clear' to reset ---\n")

conversation = []

def build_prompt(history, user_msg):
    prompt = "<|im_start|>system\nYou are an expert assistant and coder. Always provide complete, working code when requested.<|im_end|>\n"
    for turn in history:
        prompt += f"<|im_start|>{turn['role']}\n{turn['content']}<|im_end|>\n"
    prompt += f"<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n"
    return prompt

while True:
    try:
        user_input = input(">>> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        if user_input.lower() == "clear":
            conversation = []
            print("\n[Chat memory cleared!]\n")
            continue

        prompt = build_prompt(conversation, user_input)
        reply = generate(model, tokenizer, prompt=prompt, max_tokens=1000)
        print(f"\nAI:\n{reply.strip()}\n{'-'*40}\n")

        conversation.append({"role": "user", "content": user_input})
        conversation.append({"role": "assistant", "content": reply.strip()})

    except KeyboardInterrupt:
        print("\nGoodbye!")
        break
