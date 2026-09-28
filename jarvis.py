import os
import ssl
import json
import subprocess
import webbrowser
import urllib.parse
import torch
import sounddevice as sd
import numpy as np
import whisper
from openai import OpenAI

# Bypass macOS SSL certificate checks
ssl._create_default_https_context = ssl._create_unverified_context

# Select Apple Silicon Metal GPU if available, else CPU
device = "mps" if torch.backends.mps.is_available() else "cpu"
use_fp16 = True if device == "mps" else False

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="empty")

print(f"Loading Whisper 'large-v3-turbo' on device: [{device}]...")
stt_model = whisper.load_model("large-v3-turbo", device=device)

SYSTEM_PROMPT = """You are JARVIS, an autonomous AI operating system controller for macOS.
Analyze the user's voice command and respond strictly in JSON format.

Supported Actions:
1. open_app: When asked to open an application (e.g. Safari, Notes, Terminal, Spotify, Calculator).
2. open_url: When asked to open a specific website (e.g. youtube.com, github.com).
3. search_web: When asked to search or look something up online.
4. speak_answer: For general questions, conversation, or math.

Output format must ONLY be valid JSON with no markdown wrapping:
{"action": "open_app", "target": "Safari", "speech": "Opening Safari for you, sir."}
{"action": "open_url", "target": "https://www.youtube.com", "speech": "Launching YouTube."}
{"action": "search_web", "target": "space news", "speech": "Searching Google for space news."}
{"action": "speak_answer", "target": "", "speech": "Direct spoken answer here."}
"""

def speak(text):
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    os.system(f'say "{clean_text}"')

def record_audio(duration=5, fs=16000):
    print("\nListening (5 seconds)...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    audio = audio.flatten()
    
    max_val = np.max(np.abs(audio))
    if max_val > 0.01:
        audio = audio / max_val * 0.9
    return audio

def execute_action(action, target):
    try:
        if action == "open_app":
            subprocess.run(["open", "-a", target], check=True)
        elif action == "open_url":
            if not target.startswith("http"):
                target = "https://" + target
            webbrowser.open(target)
        elif action == "search_web":
            query = urllib.parse.quote_plus(target)
            webbrowser.open(f"https://www.google.com/search?q={query}")
    except Exception as e:
        print(f"Action Execution Error: {e}")

def process_command(prompt):
    response = client.chat.completions.create(
        model="default_model",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.1
    )
    raw_output = response.choices[0].message.content.strip()
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`").replace("json\n", "").replace("json", "").strip()
    try:
        data = json.loads(raw_output)
    except Exception:
        data = {"action": "speak_answer", "target": "", "speech": raw_output}
    return data

if __name__ == "__main__":
    speak("High speed core ready.")
    while True:
        try:
            input("\nPress [Enter] to speak (or Ctrl+C to quit)...")
            audio = record_audio(duration=5)
            
            print("Transcribing (Turbo Engine)...")
            result = stt_model.transcribe(
                audio, 
                fp16=use_fp16,
                language="en",
                initial_prompt="Open Safari, open YouTube, Google search, launch terminal, Mac OS system commands."
            )
            user_text = result["text"].strip()
            
            if not user_text:
                print("No speech detected.")
                continue
                
            print(f"You said: {user_text}")
            print("Processing command...")
            
            decision = process_command(user_text)
            action = decision.get("action", "speak_answer")
            target = decision.get("target", "")
            speech_text = decision.get("speech", "")
            
            print(f"Action: {action} | Target: {target}")
            print(f"JARVIS: {speech_text}\n")
            
            speak(speech_text)
            execute_action(action, target)
            
        except KeyboardInterrupt:
            speak("Powering down.")
            print("\nShutting down.")
            break
