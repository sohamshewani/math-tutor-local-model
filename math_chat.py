import re
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="none", timeout=180.0)

SUP_MAP = str.maketrans("0123456789+-=()ni", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ")
SUB_MAP = str.maketrans("0123456789+-=()aeoxhklmnpst", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ")

def format_math_output(text: str) -> str:
    # 1. Strip boxed and environment tags
    text = re.sub(r'\\boxed\{([^}]+)\}', r'[\1]', text)
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\n\1\n', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'\1', text)
    text = text.replace('\\[', '').replace('\\]', '').replace('\\(', '').replace('\\)', '')
    text = text.replace('$$', '\n').replace('$', '')

    # 2. Convert degrees and angles
    text = re.sub(r'\^\\circ|\^\{\\circ\}|\\circ', '°', text)

    # 3. Clean standard functions & trig
    for fn in ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'log', 'ln']:
        text = re.sub(rf'\\{fn}\b', fn, text)

    # 4. Standard math signs of operation & Greek letters
    replacements = {
        r'\times': ' × ', r'\div': ' ÷ ', r'\cdot': ' · ', r'\pm': ' ± ', r'\mp': ' ∓ ',
        r'\le': ' ≤ ', r'\ge': ' ≥ ', r'\neq': ' ≠ ', r'\approx': ' ≈ ',
        r'\sum': '∑', r'\prod': '∏', r'\pi': 'π', r'\Delta': 'Δ',
        r'\alpha': 'α', r'\beta': 'β', r'\theta': 'θ', r'\phi': 'φ',
        r'\implies': ' => ', r'\to': ' → ', r'\quad': '  '
    }
    for latex, symbol in replacements.items():
        text = text.replace(latex, symbol)

    # 5. Simplify fractions, binomials, and square roots
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1 / \2)', text)
    text = re.sub(r'\\binom\{([^}]+)\}\{([^}]+)\}', r'C(\1, \2)', text)
    text = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', text)
    text = text.replace(r'\sqrt', '√')

    # 6. Unicode Superscripts (^6 or ^{12} -> ⁶ or ¹²)
    text = re.sub(r'\^\{([^}]+)\}', lambda m: m.group(1).translate(SUP_MAP), text)
    text = re.sub(r'\^([0-9a-zA-Z+-])', lambda m: m.group(1).translate(SUP_MAP), text)

    # 7. Unicode Subscripts (_1 or _{12} -> ₁ or ₁₂)
    text = re.sub(r'_\{([^}]+)\}', lambda m: m.group(1).translate(SUB_MAP), text)
    text = re.sub(r'_([0-9a-zA-Z+-])', lambda m: m.group(1).translate(SUB_MAP), text)

    # 8. Clean residual stray slashes and whitespace
    text = text.replace('\\', '')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()

system_prompt = (
    "You are an expert mathematics tutor specializing in Algebra, Trigonometry, and Geometry. "
    "Provide clear, rigorous, step-by-step analytical solutions. "
    "Never stop at an approximation when an exact radical/fraction form exists (e.g., using 45°-33° or 30°-18°). "
    "Compute all values completely down to simplest radical/fraction form without leaving intermediate steps incomplete. "
    "Conclude every answer with an explicit: 'Final Answer: [exact result]'"
)

conversation_history = [{"role": "system", "content": system_prompt}]

print("=====================================================")
print("  MATH SOLVER PRO (High-Precision Math Engine)       ")
print("  - Proper math signs (+, -, ×, ÷, √, °)             ")
print("  - Unicode superscripts & subscripts (x⁶, x₁)       ")
print("  - Exact complete derivations (no cutoffs)          ")
print("  - Type 'clear' to reset | Type 'exit' to quit     ")
print("=====================================================")

while True:
    try:
        problem = input("\nEnter Math Problem: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        break

    if not problem or problem.lower() == 'exit':
        break
        
    if problem.lower() == 'clear':
        conversation_history = [{"role": "system", "content": system_prompt}]
        print("[Conversation history reset]")
        continue

    conversation_history.append({"role": "user", "content": problem})

    try:
        print("Computing exact mathematical solution...", end="", flush=True)
        response = client.chat.completions.create(
            model="default_model",
            messages=conversation_history,
            max_tokens=4000,
            temperature=0.1
        )
        print("\r" + " " * 42 + "\r", end="")

        raw_reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": raw_reply})

        cleaned_solution = format_math_output(raw_reply)
        print("\n--- Solution ---")
        print(cleaned_solution)
        print("----------------")
    except Exception as e:
        print(f"\nServer error: {e}")
