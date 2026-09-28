import tkinter as tk
from tkinter import font
import time

class DigitalClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Clock")
        self.root.geometry("300x100")
        self.root.resizable(False, False)

        self.label = tk.Label(root, font=("Arial", 40), bg="black", fg="white")
        self.label.pack(pady=20)

        self.update_time()

    def update_time(self):
        current_time = time.strftime('%H:%M:%S')
        self.label.config(text=current_time)
        self.root.after(1000, self.update_time)

if __name__ == "__main__":
    root = tk.Tk()
    clock = DigitalClock(root)
    root.mainloop()
