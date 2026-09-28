from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__)
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Matrix Planner">
  <title>Tactical Schedule Matrix</title>
  <style>
    :root {
      --bg: #0d1117;
      --card: #161b22;
      --border: #30363d;
      --cyan: #00e5ff;
      --green: #2ea043;
      --red: #ff7b72;
      --text: #f0f6fc;
      --subtext: #8b949e;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 16px; padding-bottom: 60px; max-width: 600px; margin: auto; }
    
    header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
    h1 { font-size: 1.1rem; color: var(--cyan); letter-spacing: 0.5px; }
    
    .timer-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 16px; }
    .timer-display { font-size: 2.8rem; font-weight: bold; color: var(--text); font-variant-numeric: tabular-nums; margin: 8px 0; }
    .btn-row { display: flex; gap: 8px; justify-content: center; }
    
    button { background: var(--card); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    button:active { transform: scale(0.97); }
    button.primary { background: var(--green); border-color: var(--green); color: #fff; }
    button.timer-btn { background: #1f6feb; border-color: #1f6feb; color: #fff; }
    
    .input-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 16px; }
    input, select { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px; border-radius: 8px; margin-bottom: 10px; font-size: 0.95rem; }
    input:focus, select:focus { outline: none; border-color: var(--cyan); }
    
    .task-list { display: flex; flex-direction: column; gap: 10px; }
    .task-item { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; display: flex; justify-content: space-between; align-items: center; }
    .task-item.completed { opacity: 0.5; border-color: #238636; }
    .task-item.completed .task-title { text-decoration: line-through; color: #7ee787; }
    .task-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }
    .task-meta { font-size: 0.8rem; color: var(--subtext); }
    .task-actions { display: flex; gap: 6px; }
    .del-btn { color: var(--red); border-color: rgba(255,123,114,0.3); padding: 6px 10px; }
    .check-btn { color: #7ee787; border-color: rgba(126,231,135,0.3); padding: 6px 10px; }
  </style>
</head>
<body>

  <header>
    <h1>⚡ TACTICAL MATRIX</h1>
    <span id="date-label" style="font-size:0.8rem; color:var(--subtext);"></span>
  </header>

  <!-- Focus Timer Module -->
  <div class="timer-card">
    <div style="font-size: 0.85rem; color: var(--red); font-weight: bold; letter-spacing: 1px;">POMODORO FOCUS</div>
    <div class="timer-display" id="timer">25:00</div>
    <div class="btn-row">
      <button class="timer-btn" id="startBtn" onclick="toggleTimer()">Start</button>
      <button onclick="resetTimer()">Reset</button>
    </div>
  </div>

  <!-- Add Task Form -->
  <div class="input-card">
    <input type="text" id="taskInput" placeholder="Subject or task name...">
    <div style="display:flex; gap:8px;">
      <select id="catSelect">
        <option value="Mathematics">Mathematics</option>
        <option value="Science">Science</option>
        <option value="Programming">Programming</option>
        <option value="Workout">Workout</option>
        <option value="Revision">Revision</option>
      </select>
      <input type="text" id="timeInput" placeholder="Time slot (e.g. 6-7 PM)">
    </div>
    <button class="primary" style="width: 100%; padding: 10px;" onclick="addTask()">+ Add to Schedule</button>
  </div>

  <!-- Task Stream -->
  <div class="task-list" id="taskList"></div>

  <script>
    document.getElementById('date-label').innerText = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

    async function loadTasks() {
      const res = await fetch('/api/tasks');
      const tasks = await res.json();
      const list = document.getElementById('taskList');
      list.innerHTML = '';
      tasks.forEach(t => {
        const item = document.createElement('div');
        item.className = 'task-item ' + (t.status === 'Completed' ? 'completed' : '');
        item.innerHTML = `
          <div>
            <div class="task-title">${t.title}</div>
            <div class="task-meta">${t.category} • ${t.time_slot}</div>
          </div>
          <div class="task-actions">
            <button class="check-btn" onclick="toggleStatus(${t.id}, '${t.status}')">✓</button>
            <button class="del-btn" onclick="deleteTask(${t.id})">✕</button>
          </div>
        `;
        list.appendChild(item);
      });
    }

    async function addTask() {
      const title = document.getElementById('taskInput').value.trim();
      const category = document.getElementById('catSelect').value;
      const time_slot = document.getElementById('timeInput').value.trim() || 'Flexible';
      if (!title) return;
      await fetch('/api/tasks', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, category, time_slot})
      });
      document.getElementById('taskInput').value = '';
      loadTasks();
    }

    async function toggleStatus(id, current) {
      const next = current === 'Completed' ? 'Pending' : 'Completed';
      await fetch(`/api/tasks/${id}/status`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status: next})
      });
      loadTasks();
    }

    async function deleteTask(id) {
      await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
      loadTasks();
    }

    // Pomodoro Engine
    let totalSecs = 25 * 60;
    let timerRunning = false;
    let timerInterval = null;

    function updateTimerDisplay() {
      const m = Math.floor(totalSecs / 60).toString().padStart(2, '0');
      const s = (totalSecs % 60).toString().padStart(2, '0');
      document.getElementById('timer').innerText = `${m}:${s}`;
    }

    function toggleTimer() {
      const btn = document.getElementById('startBtn');
      if (timerRunning) {
        clearInterval(timerInterval);
        timerRunning = false;
        btn.innerText = 'Start';
        btn.style.background = '#1f6feb';
      } else {
        timerRunning = true;
        btn.innerText = 'Pause';
        btn.style.background = '#d29922';
        timerInterval = setInterval(() => {
          if (totalSecs > 0) {
            totalSecs--;
            updateTimerDisplay();
          } else {
            clearInterval(timerInterval);
            timerRunning = false;
            alert('Focus session complete!');
            resetTimer();
          }
        }, 1000);
      }
    }

    function resetTimer() {
      clearInterval(timerInterval);
      timerRunning = false;
      totalSecs = 25 * 60;
      document.getElementById('startBtn').innerText = 'Start';
      document.getElementById('startBtn').style.background = '#1f6feb';
      updateTimerDisplay();
    }

    loadTasks();
  </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, category, time_slot, status FROM tasks ORDER BY id DESC")
    rows = [{"id": r[0], "title": r[1], "category": r[2], "time_slot": r[3], "status": r[4]} for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (title, category, time_slot, status) VALUES (?, ?, ?, 'Pending')",
              (data['title'], data['category'], data['time_slot']))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/tasks/<int:task_id>/status', methods=['POST'])
def update_status(task_id):
    new_status = request.json['status']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    # Binds to 0.0.0.0 so devices on your Wi-Fi network can connect
    app.run(host='0.0.0.0', port=5001, debug=False)
