import sqlite3

conn = sqlite3.connect("jarvis_memory.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS timetable")
cursor.execute("""
CREATE TABLE timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_or_time TEXT,
    activity TEXT
)
""")

# Load routine schedule entries
schedule = [
    ("06:30 AM", "Morning wake up and hydration"),
    ("07:00 AM", "Gym workout - chest, core, and cardio finish"),
    ("09:00 AM", "Academics - Algebra, Trigonometry, and Science revision"),
    ("12:00 PM", "Python software development, Tkinter GUI builds, and coding practice"),
    ("05:00 PM", "Evening recreation, rooftop cricket, and outdoor break"),
    ("08:00 PM", "Dinner and relaxation"),
    ("10:30 PM", "Night wind-down and sleep")
]

cursor.executemany("INSERT INTO timetable (day_or_time, activity) VALUES (?, ?)", schedule)
conn.commit()
conn.close()
print("Timetable database initialized with complete routine.")
