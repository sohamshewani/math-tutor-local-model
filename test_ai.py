from mlx_lm import load, generate

print("Loading fine-tuned model...")
model, tokenizer = load(
    "mlx-community/Qwen2.5-7B-Instruct-4bit",
    adapter_path="adapters"
)

prompt = "<|im_start|>user\nWrite a short Python function to calculate compound interest.<|im_end|>\n<|im_start|>assistant\n"

print("\nGenerating response:\n")
response = generate(model, tokenizer, prompt=prompt, max_tokens=150)
print(response)
