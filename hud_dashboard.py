import psutil
import requests
import re
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.reactive import reactive
from textual import on

SUP_MAP = str.maketrans("0123456789+-=()ni", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ")
SUB_MAP = str.maketrans("0123456789+-=()aeoxhklmnpst", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ")

def format_math_output(text: str) -> str:
    text = re.sub(r'\\\[(.*?)\\\]', r'\n\1\n', text, flags=re.DOTALL)
    text = re.sub(r'\\\((.*?)\\\)', r'\1', text)
    text = text.replace('\\[', '').replace('\\]', '').replace('\\(', '').replace('\\)', '')
    text = text.replace('$$', '\n').replace('$', '')
    for fn in ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'log', 'ln']:
        text = re.sub(rf'\\{fn}\b', fn, text)
    replacements = {
        r'\times': ' × ', r'\div': ' ÷ ', r'\pm': ' ± ', r'\approx': ' ≈ ',
        r'\pi': 'π', r'\sqrt': '√', r'\implies': ' => ', r'\to': ' → '
    }
    for latex, symbol in replacements.items():
        text = text.replace(latex, symbol)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1 / \2)', text)
    text = re.sub(r'\^\{([^}]+)\}', lambda m: m.group(1).translate(SUP_MAP), text)
    text = re.sub(r'\^([0-9a-zA-Z+-])', lambda m: m.group(1).translate(SUP_MAP), text)
    text = re.sub(r'_\{([^}]+)\}', lambda m: m.group(1).translate(SUB_MAP), text)
    text = re.sub(r'_([0-9a-zA-Z+-])', lambda m: m.group(1).translate(SUB_MAP), text)
    return text.replace('\\', '').strip()

class TelemetryWidget(Static):
    cpu_val = reactive("0.0%")
    ram_val = reactive("0.0%")
    ai_status = reactive("OFFLINE")

    def render(self) -> str:
        status_color = "green" if "ACTIVE" in self.ai_status else "red"
        return (
            f"[bold cyan]SYSTEM TELEMETRY[/bold cyan]\n\n"
            f"[bold white]CPU Load:[/bold white]     [yellow]{self.cpu_val}[/yellow]\n"
            f"[bold white]RAM Usage:[/bold white]    [magenta]{self.ram_val}[/magenta]\n\n"
            f"[bold cyan]AI CORE (Port 8080)[/bold cyan]\n"
            f"[bold white]Status:[/bold white]       [{status_color}]{self.ai_status}[/{status_color}]\n"
            f"[bold white]Engine:[/bold white]       Qwen2.5-7B LoRA\n"
            f"[bold white]Time:[/bold white]         [cyan]{datetime.now().strftime('%H:%M:%S')}[/cyan]"
        )

class CyberHUD(App):
    CSS = """
    Screen {
        background: #0d1117;
    }
    #main_layout {
        height: 1fr;
    }
    #sidebar {
        width: 32;
        border: heavy cyan;
        padding: 1;
        background: #161b22;
    }
    #chat_area {
        width: 1fr;
        border: heavy green;
        padding: 1;
        background: #0d1117;
    }
    #log_view {
        height: 1fr;
        background: #0d1117;
    }
    #user_input {
        dock: bottom;
        border: solid cyan;
        background: #161b22;
        color: white;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main_layout"):
            with Vertical(id="sidebar"):
                yield TelemetryWidget(id="telemetry")
            with Vertical(id="chat_area"):
                yield RichLog(id="log_view", wrap=True, highlight=True, markup=True)
                yield Input(placeholder="Ask your fine-tuned model or run math problem...", id="user_input")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_telemetry)
        log = self.query_one(RichLog)
        log.write("[bold green]=== CYBER-TERMINAL HUD v1.0 ONLINE ===[/bold green]")
        log.write("[dim]Type your question or math equation below and press Enter.[/dim]\n")

    def update_telemetry(self) -> None:
        telemetry = self.query_one(TelemetryWidget)
        telemetry.cpu_val = f"{psutil.cpu_percent():.1f}%"
        telemetry.ram_val = f"{psutil.virtual_memory().percent:.1f}%"

        try:
            r = requests.get("http://127.0.0.1:8080/v1/models", timeout=0.5)
            telemetry.ai_status = "ACTIVE [8080]" if r.status_code == 200 else "STANDBY"
        except:
            telemetry.ai_status = "OFFLINE"

    @on(Input.Submitted, "#user_input")
    def handle_submit(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return
            
        inp = self.query_one(Input)
        inp.value = ""
        log = self.query_one(RichLog)

        log.write(f"\n[bold cyan]User ❯[/bold cyan] {user_text}")

        try:
            payload = {
                "model": "default_model",
                "messages": [
                    {"role": "system", "content": "You are an expert math tutor. Provide rigorous, step-by-step derivations."},
                    {"role": "user", "content": user_text}
                ],
                "max_tokens": 1200,
                "temperature": 0.1
            }
            r = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload, timeout=60)
            if r.status_code == 200:
                raw = r.json()["choices"][0]["message"]["content"]
                formatted = format_math_output(raw)
                log.write(f"[bold green]AI Response ❯[/bold green]\n{formatted}\n")
            else:
                log.write(f"[bold red]AI Server Error:[/bold red] Status {r.status_code}")
        except Exception:
            log.write("[bold red]Connection Error:[/bold red] Make sure mlx_lm.server is running on port 8080.")

if __name__ == "__main__":
    app = CyberHUD()
    app.run()
