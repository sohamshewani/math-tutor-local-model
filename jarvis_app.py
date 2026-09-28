import os
import ssl
import sys
import math
import time
import json
import sqlite3
import threading
import subprocess
import webbrowser
import urllib.parse
import tkinter as tk
import torch
import sounddevice as sd
import numpy as np
import whisper
from openai import OpenAI
from duckduckgo_search import DDGS

ssl._create_default_https_context = ssl._create_unverified_context

# Hardware acceleration: Metal Performance Shaders (Apple Silicon GPU)
device = "mps" if torch.backends.mps.is_available() else "cpu"
use_fp16 = True if device == "mps" else False

print(f"[BOOT] Initializing JARVIS Core on hardware device: [{device}]...")
stt_model = whisper.load_model("base.en", device=device)
client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="empty")

SYSTEM_PROMPT = """You are JARVIS, an articulate and powerful artificial intelligence operating system controller for macOS.
Convert user speech into actionable commands and respond STRICTLY in JSON.

Supported Actions:
1. "open_app": Target is the exact Mac application name (e.g. "Safari", "Calculator", "Visual Studio Code", "Notes", "Terminal", "Music", "System Settings").
2. "open_url": Target is a full web URL (e.g. "https://www.youtube.com", "https://www.google.com").
3. "search_web": Target is the explicit web query to search online.
4. "set_volume": Target is an integer from 0 to 100 representing macOS system volume.
5. "get_schedule": Target is empty; used whenever asked about timetable, schedule, routine, or tasks.
6. "speak_answer": Target is empty; used for knowledge, calculation, advice, or general conversation.

Output schema:
{"action": "<action_name>", "target": "<target_value>", "speech": "<crisp, polished spoken reply>"}

DO NOT output markdown backticks. Return raw JSON only."""

def speak(text):
    clean = text.replace('"', '').replace("'", "").replace("\n", " ").strip()
    print(f"\n[JARVIS]: {clean}")
    os.system(f'say -v Samantha "{clean}" &')

def query_live_web(query):
    try:
        results = list(DDGS().text(query, max_results=3))
        if results:
            return " ".join([r["body"] for r in results[:2]])[:450]
    except Exception as e:
        print(f"[SEARCH ERROR]: {e}")
    return "No live information could be retrieved."

def query_timetable():
    try:
        conn = sqlite3.connect("jarvis_memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT day_or_time, activity FROM timetable")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            return "Here is your routine: " + "; ".join([f"{t}: {a}" for t, a in rows])
    except Exception as e:
        print(f"[DB ERROR]: {e}")
    return "No timetable entries found in your local database."

def execute_mac_action(action, target):
    try:
        if action == "open_app":
            subprocess.run(["open", "-a", target], check=False)
        elif action == "open_url":
            if not target.startswith("http"):
                target = "https://" + target
            webbrowser.open(target)
        elif action == "search_web":
            q = urllib.parse.quote_plus(target)
            webbrowser.open(f"https://www.google.com/search?q={q}")
        elif action == "set_volume":
            try:
                vol = int(target)
                os.system(f"osascript -e 'set volume output volume {vol}'")
            except Exception:
                pass
    except Exception as e:
        print(f"[SYSTEM EXEC ERROR]: {e}")

# ==================== Marvel Arc Reactor HUD ====================
class MarvelHUD:
    def __init__(self, root):
        self.root = root
        self.root.title("STARK INDUSTRIES — J.A.R.V.I.S. INTERFACE")
        self.root.geometry("640x760")
        self.root.configure(bg="#02070d")
        self.root.resizable(False, False)

        self.title_label = tk.Label(root, text="MARK VII // J.A.R.V.I.S. ONLINE", 
                                    font=("Courier New", 12, "bold"), fg="#00f2ff", bg="#02070d")
        self.title_label.pack(pady=(12, 0))

        self.canvas = tk.Canvas(root, width=600, height=480, bg="#02070d", highlightthickness=0)
        self.canvas.pack()

        self.status_label = tk.Label(root, text="CORE: ONLINE // SAY 'HEY JARVIS'", 
                                     font=("Helvetica Neue", 12, "bold"), fg="#00e5ff", bg="#02070d")
        self.status_label.pack(pady=4)

        self.sub_label = tk.Label(root, text="Auditory neural arrays active. Awaiting wake word...", 
                                  font=("Courier New", 10), fg="#3a7d99", bg="#02070d", wraplength=580)
        self.sub_label.pack(pady=4)

        self.btn = tk.Button(root, text="⚡ CLICK TO SPEAK (OR SAY 'HEY JARVIS') ⚡", 
                             font=("Helvetica Neue", 11, "bold"), bg="#00e5ff", fg="#02070d",
                             activebackground="#ff3355", padx=20, pady=8, relief="flat",
                             command=self.manual_trigger)
        self.btn.pack(pady=8)

        self.angle_outer = 0
        self.angle_inner = 0
        self.pulse = 0
        self.pulse_dir = 1
        self.state = "standby"
        self.running = True
        self.is_busy = False

        self.animate_hud()

    def set_state(self, state, status_text, sub_text=""):
        self.state = state
        self.status_label.config(text=status_text)
        if sub_text:
            self.sub_label.config(text=sub_text)

        color_map = {
            "standby": "#00e5ff",
            "listening": "#00ff66",
            "processing": "#ffaa00",
            "speaking": "#ff3355"
        }
        self.status_label.config(fg=color_map.get(state, "#00e5ff"))

    def manual_trigger(self):
        if not self.is_busy:
            threading.Thread(target=process_active_command, args=(self,), daemon=True).start()

    def animate_hud(self):
        if not self.running:
            return
        self.canvas.delete("all")
        cx, cy = 300, 240

        palette = {
            "standby": ("#00e5ff", "#005577", "#002233"),
            "listening": ("#00ff77", "#007733", "#003311"),
            "processing": ("#ffb700", "#775500", "#332200"),
            "speaking": ("#ff2a55", "#771122", "#330811")
        }
        accent, mid, dark = palette.get(self.state, palette["standby"])

        for r in [210, 170, 130, 95, 65]:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=dark, width=1)

        num_outer = 36
        for i in range(num_outer):
            if i % 3 != 0:
                rad = math.radians(i * (360 / num_outer) + self.angle_outer)
                x1 = cx + 195 * math.cos(rad)
                y1 = cy + 195 * math.sin(rad)
                x2 = cx + 208 * math.cos(rad)
                y2 = cy + 208 * math.sin(rad)
                self.canvas.create_line(x1, y1, x2, y2, fill=mid, width=2)

        num_inner = 24
        for i in range(num_inner):
            rad = math.radians(i * (360 / num_inner) - self.angle_inner)
            x1 = cx + 145 * math.cos(rad)
            y1 = cy + 145 * math.sin(rad)
            x2 = cx + 160 * math.cos(rad)
            y2 = cy + 160 * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=accent, width=2 if i % 2 == 0 else 1)

        for offset_angle in [0, 120, 240]:
            pts = []
            for vertex_angle in [0, 120, 240]:
                rad = math.radians(vertex_angle + offset_angle + (self.angle_outer * 0.5))
                pts.append(cx + 85 * math.cos(rad))
                pts.append(cy + 85 * math.sin(rad))
            self.canvas.create_polygon(pts, outline=mid, fill="", width=1)

        core_r = 45 + self.pulse
        self.canvas.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r, outline=accent, width=3)
        self.canvas.create_text(cx, cy, text="JARVIS", fill=accent, font=("Helvetica Neue", 13, "bold"))

        self.angle_outer = (self.angle_outer + 1.5) % 360
        self.angle_inner = (self.angle_inner + 2.5) % 360
        self.pulse += 0.35 * self.pulse_dir
        if self.pulse > 5 or self.pulse < -3:
            self.pulse_dir *= -1

        self.root.after(35, self.animate_hud)

# ==================== Real-Time High-Speed Audio Stream ====================
def record_speech_segment(fs=16000, duration=4.5):
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    audio = audio.flatten()
    peak = np.max(np.abs(audio))
    if peak > 0.01:
        audio = audio / peak * 0.95
    return audio

def process_active_command(hud, existing_audio=None):
    hud.is_busy = True
    try:
        if existing_audio is None:
            hud.set_state("listening", "LISTENING...", "State your command clearly...")
            audio = record_speech_segment(duration=4.5)
        else:
            audio = existing_audio

        hud.set_state("processing", "TRANSCRIBING...", "Decoding Metal GPU waveform...")
        res = stt_model.transcribe(audio, fp16=use_fp16, language="en")
        raw_text = res["text"].strip()
        print(f"\n[USER HEARD]: '{raw_text}'")

        if len(raw_text) < 2:
            hud.set_state("standby", "CORE: ONLINE", "No command received.")
            hud.is_busy = False
            return

        clean_text = raw_text.lower()
        for w in ["hey jarvis", "jarvis", "hey"]:
            clean_text = clean_text.replace(w, "").strip()

        if len(clean_text) < 2:
            hud.set_state("listening", "LISTENING...", "Yes sir? I am listening.")
            speak("Yes sir, what would you like me to do?")
            time.sleep(1.2)
            audio = record_speech_segment(duration=4.5)
            res = stt_model.transcribe(audio, fp16=use_fp16, language="en")
            clean_text = res["text"].strip()
            print(f"[FOLLOW-UP HEARD]: '{clean_text}'")

        if not clean_text or len(clean_text) < 2:
            hud.set_state("standby", "CORE: ONLINE", "Awaiting wake word.")
            hud.is_busy = False
            return

        hud.set_state("processing", "REASONING...", f"Command: '{clean_text}'")

        response = client.chat.completions.create(
            model="default_model",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": clean_text}
            ],
            max_tokens=250,
            temperature=0.1
        )
        raw_json = response.choices[0].message.content.strip()
        if raw_json.startswith("```"):
            raw_json = raw_json.strip("`").replace("json\n", "").replace("json", "").strip()

        try:
            data = json.loads(raw_json)
        except Exception:
            data = {"action": "speak_answer", "target": "", "speech": raw_json}

        action = data.get("action", "speak_answer")
        target = data.get("target", "")
        speech_text = data.get("speech", "")

        # Fallback system matching
        if "safari" in clean_text.lower():
            action, target = "open_app", "Safari"
        elif "youtube" in clean_text.lower():
            action, target = "open_url", "[https://www.youtube.com](https://www.youtube.com)"
        elif any(k in clean_text.lower() for k in ["timetable", "schedule", "routine"]):
            action = "get_schedule"

        # Action execution
        if action == "get_schedule":
            speech_text = query_timetable()
        elif action == "search_web":
            execute_mac_action("search_web", target if target else clean_text)
            web_info = query_live_web(target if target else clean_text)
            ai_summary = client.chat.completions.create(
                model="default_model",
                messages=[
                    {"role": "system", "content": "You are JARVIS. Give a crisp, polished 2-sentence summary."},
                    {"role": "user", "content": f"Query: {clean_text}\nData: {web_info}"}
                ],
                max_tokens=150
            )
            speech_text = ai_summary.choices[0].message.content.strip()
        elif action in ["open_app", "open_url", "set_volume"]:
            execute_mac_action(action, target)

        hud.set_state("speaking", "J.A.R.V.I.S. RESPONDING", speech_text)
        speak(speech_text)
        time.sleep(3.0)

    except Exception as e:
        print(f"[EXEC ERROR]: {e}")
    finally:
        hud.set_state("standby", "CORE: ONLINE // SAY 'HEY JARVIS'", "Awaiting voice command...")
        hud.is_busy = False

def continuous_wake_listener(hud):
    """Zero-delay sliding-window wake-word listener."""
    fs = 16000
    chunk_sec = 2.0
    while hud.running:
        if hud.is_busy:
            time.sleep(0.5)
            continue
        try:
            chunk = sd.rec(int(fs * chunk_sec), samplerate=fs, channels=1, dtype='float32')
            sd.wait()
            vol = np.max(np.abs(chunk))

            # Only process if human voice volume threshold reached
            if vol > 0.035 and not hud.is_busy:
                res = stt_model.transcribe(chunk.flatten(), fp16=use_fp16, language="en")
                heard = res["text"].strip().lower()

                # Flexible wake word phonetic matching
                if any(w in heard for w in ["jarvis", "hey jarvis", "service", "harvest", "jarves"]):
                    print(f"\n[WAKE WORD TRIGGERED: '{heard}'] Activating JARVIS...")
                    process_active_command(hud)

        except Exception as e:
            time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    hud = MarvelHUD(root)
    threading.Thread(target=continuous_wake_listener, args=(hud,), daemon=True).start()
    speak("Systems calibrated. JARVIS online.")
    root.mainloop()
