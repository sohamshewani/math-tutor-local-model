import sys
import re
import requests
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QLabel, QPushButton, QGraphicsDropShadowEffect
)

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

class SpotlightHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()
        self.init_ui()

    def init_ui(self):
        # Native macOS floating tool palette flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(660, 490)

        container = QWidget(self)
        container.setObjectName("container")
        container.setGeometry(10, 10, 640, 470)
        container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(15, 20, 30, 0.96);
                border: 2px solid #00e5ff;
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 229, 255, 140))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("AI SPOTLIGHT HUD // QWEN CORE", self)
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #00e5ff; letter-spacing: 1.5px;")
        
        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #21262d;
                color: #8b949e;
                font-weight: bold;
                border: 1px solid #30363d;
                border-radius: 13px;
            }
            QPushButton:hover {
                background: #ff5f56;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Enter problem (e.g. solve x^2 - 7x + 12 = 0)...")
        self.input_field.setFont(QFont("Menlo", 13))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1.5px solid #30363d;
                border-radius: 8px;
                padding: 10px;
                color: #f0f6fc;
            }
            QLineEdit:focus {
                border: 1.5px solid #00e5ff;
            }
        """)
        self.input_field.returnPressed.connect(self.query_model)
        layout.addWidget(self.input_field)

        self.output_area = QTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Menlo", 12))
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
                padding: 12px;
                color: #58a6ff;
            }
        """)
        layout.addWidget(self.output_area)

        bottom = QHBoxLayout()
        hint = QLabel("Press ESC to exit | Drag to move", self)
        hint.setFont(QFont("Arial", 10))
        hint.setStyleSheet("color: #8b949e;")

        copy_btn = QPushButton("Copy Output", self)
        copy_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #00e5ff;
                color: #0d1117;
            }
        """)
        copy_btn.clicked.connect(self.copy_to_clipboard)

        bottom.addWidget(hint)
        bottom.addStretch()
        bottom.addWidget(copy_btn)
        layout.addLayout(bottom)

        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 3)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.output_area.toPlainText())

    def query_model(self):
        query = self.input_field.text().strip()
        if not query:
            return

        self.output_area.setPlainText("Deriving step-by-step mathematical solution...")
        QApplication.processEvents()

        try:
            payload = {
                "model": "default_model",
                "messages": [
                    {"role": "system", "content": "You are a high-speed mathematics engine. Provide concise, step-by-step derivations with clean answers."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 1500,
                "temperature": 0.1
            }
            res = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload, timeout=60)
            if res.status_code == 200:
                raw = res.json()["choices"][0]["message"]["content"]
                self.output_area.setPlainText(format_math_output(raw))
            else:
                self.output_area.setPlainText(f"Server Error: Status {res.status_code}")
        except Exception as e:
            self.output_area.setPlainText(f"Connection Error: {e}\nEnsure mlx_lm.server is listening on port 8080.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpotlightHUD()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())
