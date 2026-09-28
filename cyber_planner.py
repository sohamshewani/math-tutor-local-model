import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

# --- DATABASE SETUP ---
DB_NAME = "planner_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- MAIN GUI ---
class CyberPlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TACTICAL STUDY & SCHEDULE MATRIX")
        self.geometry("980x640")
        self.configure(bg="#0d1117")
        self.resizable(True, True)

        # Timer Variables
        self.timer_seconds = 25 * 60
        self.timer_running = False
        self.timer_id = None

        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        # 1. Top Header Bar
        header = tk.Frame(self, bg="#161b22", height=60, bd=0)
        header.pack(fill="x", side="top")
        
        title_lbl = tk.Label(
            header, text="⚡ DAILY SCHEDULE & TACTICAL PLANNER",
            font=("Arial", 14, "bold"), fg="#00e5ff", bg="#161b22"
        )
        title_lbl.pack(side="left", padx=20, pady=15)

        date_lbl = tk.Label(
            header, text=datetime.datetime.now().strftime("%A, %d %B %Y"),
            font=("Arial", 11), fg="#8b949e", bg="#161b22"
        )
        date_lbl.pack(side="right", padx=20)

        # 2. Main Horizontal Container
        body = tk.Frame(self, bg="#0d1117")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # LEFT COLUMN: Add Task & Pomodoro Focus Timer
        left_panel = tk.Frame(body, bg="#161b22", width=320, bd=1, relief="solid")
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        # Task Input Section
        input_title = tk.Label(
            left_panel, text="ADD SCHEDULE ITEM",
            font=("Arial", 11, "bold"), fg="#00e5ff", bg="#161b22"
        )
        input_title.pack(anchor="w", padx=15, pady=(15, 10))

        tk.Label(left_panel, text="Task Name / Topic:", font=("Arial", 9), fg="#c9d1d9", bg="#161b22").pack(anchor="w", padx=15)
        self.task_entry = tk.Entry(left_panel, bg="#0d1117", fg="#f0f6fc", insertbackground="#00e5ff", relief="flat", font=("Arial", 10))
        self.task_entry.pack(fill="x", padx=15, pady=(2, 10), ipady=4)

        tk.Label(left_panel, text="Category:", font=("Arial", 9), fg="#c9d1d9", bg="#161b22").pack(anchor="w", padx=15)
        self.cat_combo = ttk.Combobox(left_panel, values=["Mathematics", "Science", "Programming", "Workout", "Revision", "General"], state="readonly")
        self.cat_combo.set("Mathematics")
        self.cat_combo.pack(fill="x", padx=15, pady=(2, 10))

        tk.Label(left_panel, text="Time Slot (e.g. 05:00 PM - 06:30 PM):", font=("Arial", 9), fg="#c9d1d9", bg="#161b22").pack(anchor="w", padx=15)
        self.time_entry = tk.Entry(left_panel, bg="#0d1117", fg="#f0f6fc", insertbackground="#00e5ff", relief="flat", font=("Arial", 10))
        self.time_entry.insert(0, "06:00 PM - 07:00 PM")
        self.time_entry.pack(fill="x", padx=15, pady=(2, 15), ipady=4)

        add_btn = tk.Button(
            left_panel, text="+ Add to Matrix",
            font=("Arial", 10, "bold"), bg="#238636", fg="white", activebackground="#2ea043",
            relief="flat", cursor="hand2", command=self.add_task
        )
        add_btn.pack(fill="x", padx=15, ipady=4)

        # Divider
        tk.Frame(left_panel, bg="#30363d", height=1).pack(fill="x", padx=15, pady=20)

        # Pomodoro Focus Module
        pomo_lbl = tk.Label(
            left_panel, text="FOCUS TIMER (25 MIN)",
            font=("Arial", 11, "bold"), fg="#ff7b72", bg="#161b22"
        )
        pomo_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        self.timer_display = tk.Label(
            left_panel, text="25:00",
            font=("Arial", 28, "bold"), fg="#f0f6fc", bg="#161b22"
        )
        self.timer_display.pack(pady=5)

        btn_row = tk.Frame(left_panel, bg="#161b22")
        btn_row.pack(fill="x", padx=15, pady=10)

        self.start_btn = tk.Button(btn_row, text="Start", font=("Arial", 9, "bold"), bg="#1f6feb", fg="white", relief="flat", cursor="hand2", width=7, command=self.toggle_timer)
        self.start_btn.pack(side="left", padx=2)

        reset_btn = tk.Button(btn_row, text="Reset", font=("Arial", 9), bg="#21262d", fg="#8b949e", relief="flat", cursor="hand2", width=7, command=self.reset_timer)
        reset_btn.pack(side="left", padx=2)

        # RIGHT COLUMN: Interactive Task Matrix & Schedule Table
        right_panel = tk.Frame(body, bg="#161b22", bd=1, relief="solid")
        right_panel.pack(side="right", fill="both", expand=True)

        table_header = tk.Frame(right_panel, bg="#161b22")
        table_header.pack(fill="x", padx=15, pady=15)

        tk.Label(table_header, text="ACTIVE TIMETABLE & TASKS", font=("Arial", 11, "bold"), fg="#00e5ff", bg="#161b22").pack(side="left")

        complete_btn = tk.Button(
            table_header, text="✓ Toggle Completed",
            font=("Arial", 9, "bold"), bg="#21262d", fg="#7ee787", relief="flat", cursor="hand2", command=self.toggle_complete
        )
        complete_btn.pack(side="right", padx=5)

        del_btn = tk.Button(
            table_header, text="✕ Delete",
            font=("Arial", 9), bg="#21262d", fg="#ff7b72", relief="flat", cursor="hand2", command=self.delete_task
        )
        del_btn.pack(side="right", padx=5)

        # Treeview Schedule Table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background="#0d1117",
            foreground="#f0f6fc",
            fieldbackground="#0d1117",
            rowheight=32,
            font=("Arial", 10)
        )
        style.configure("Treeview.Heading",
            background="#161b22",
            foreground="#00e5ff",
            font=("Arial", 10, "bold")
        )
        style.map("Treeview", background=[("selected", "#1f6feb")])

        columns = ("ID", "Time Slot", "Subject / Task", "Category", "Status")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("ID", text="#")
        self.tree.heading("Time Slot", text="Time Slot")
        self.tree.heading("Subject / Task", text="Task / Study Topic")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Status", text="Status")

        self.tree.column("ID", width=35, anchor="center")
        self.tree.column("Time Slot", width=160, anchor="w")
        self.tree.column("Subject / Task", width=220, anchor="w")
        self.tree.column("Category", width=110, anchor="center")
        self.tree.column("Status", width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # --- DATABASE OPERATIONS ---
    def load_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, time_slot, title, category, status FROM tasks ORDER BY id ASC")
        rows = c.fetchall()
        conn.close()

        for row in rows:
            tag = "completed" if row[4] == "Completed" else "pending"
            self.tree.insert("", "end", values=row, tags=(tag,))

        self.tree.tag_configure("completed", foreground="#7ee787")
        self.tree.tag_configure("pending", foreground="#f0f6fc")

    def add_task(self):
        title = self.task_entry.get().strip()
        time_slot = self.time_entry.get().strip()
        category = self.cat_combo.get()

        if not title:
            messagebox.showwarning("Incomplete", "Please enter a task name or study topic.")
            return

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (title, category, time_slot, status) VALUES (?, ?, ?, 'Pending')",
                  (title, category, time_slot))
        conn.commit()
        conn.close()

        self.task_entry.delete(0, tk.END)
        self.load_tasks()

    def toggle_complete(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = self.tree.item(selected[0])["values"][0]
        current_status = self.tree.item(selected[0])["values"][4]
        new_status = "Pending" if current_status == "Completed" else "Completed"

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
        conn.close()
        self.load_tasks()

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = self.tree.item(selected[0])["values"][0]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        self.load_tasks()

    # --- POMODORO TIMER LOGIC ---
    def toggle_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.start_btn.config(text="Start", bg="#1f6feb")
            if self.timer_id:
                self.after_cancel(self.timer_id)
        else:
            self.timer_running = True
            self.start_btn.config(text="Pause", bg="#d29922")
            self.count_down()

    def count_down(self):
        if self.timer_running:
            if self.timer_seconds > 0:
                self.timer_seconds -= 1
                mins, secs = divmod(self.timer_seconds, 60)
                self.timer_display.config(text=f"{mins:02d}:{secs:02d}")
                self.timer_id = self.after(1000, self.count_down)
            else:
                self.timer_running = False
                self.start_btn.config(text="Start", bg="#1f6feb")
                messagebox.showinfo("Focus Complete", "Pomodoro interval finished! Take a 5-minute break.")

    def reset_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.timer_running = False
        self.timer_seconds = 25 * 60
        self.timer_display.config(text="25:00")
        self.start_btn.config(text="Start", bg="#1f6feb")

if __name__ == "__main__":
    app = CyberPlanner()
    app.mainloop()
