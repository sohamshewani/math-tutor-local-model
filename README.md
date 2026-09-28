# Local Math Tutor & Continuum Physics Engine (MLX Qwen2.5)

A local suite of AI tools and real-time continuum physics simulations built with Apple Silicon MLX and PyQt6.

---

## Features

- **Fine-Tuned Local Math AI:** LoRA fine-tuned Qwen2.5-7B-Instruct-4bit model specialized in step-by-step math problem decomposition.
- **Terminal & HUD Math Chat:** 4,000+ token capacity client featuring dynamic Unicode LaTeX translation for mathematical formulas.
- **3D Viscoelastic Continuum Physics Engine:** Gravitational sphere with Hertzian contact mechanics, Kelvin-Voigt damping, volume preservation, and live FLOP telemetry.
- **Tactical Planner PWA:** Flask synchronization server for desktop and mobile task tracking.

---

## Quick Start

### 1. Environment Setup
```bash
python3 -m venv ai_env
source ai_env/bin/activate
pip install mlx-lm PyQt6 flask
