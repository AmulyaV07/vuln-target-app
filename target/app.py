import json
import os
import platform
import sqlite3

from flask import Flask, jsonify, render_template_string, request

from database import DB_PATH, fetch_all_staff, init_db

app = Flask(__name__)

HOME_HTML = """
<!DOCTYPE html>
<html>
<head><title>Random Login Page</title></head>
<body style="font-family: sans-serif; background: #eee; color: #333; padding: 2rem;">
  <h1>Company Portal Login</h1>
  <form id="loginForm">
    <label>Alias:</label><br>
    <input type="text" name="username" id="username" style="width: 300px;"><br><br>
    <label>Passcode:</label><br>
    <input type="password" name="password" id="password" style="width: 300px;"><br><br>
    <button type="submit">Access System</button>
  </form>
  <pre id="result" style="margin-top: 1rem;"></pre>
  <script>
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
    });
  </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HOME_HTML)


@app.route("/health")
def health():
    return jsonify({"status": "alive"})


@app.route("/login", methods=["POST"])
def auth_employee():
    payload = request.get_json(silent=True) or {}
    # Extracting inputs
    user_alias = payload.get("username", "")
    secret_key = payload.get("password", "")

    # Completely different coding style, using f-strings and new table
    unsafe_query = f"SELECT * FROM staff_directory WHERE emp_alias = '{user_alias}' AND secret_passcode = '{secret_key}'"

    db_conn = sqlite3.connect(DB_PATH)
    db_conn.row_factory = sqlite3.Row
    cursor = db_conn.cursor()
    try:
        cursor.execute(unsafe_query)
        fetched_data = cursor.fetchall()
    except sqlite3.Error:
        db_conn.close()
        return jsonify({"status": "fail"})

    db_conn.close()

    if not fetched_data:
        return jsonify({"status": "fail"})

    if len(fetched_data) > 1:
        staff_dump = [dict(r) for r in fetched_data]
        return jsonify({"status": "success", "users": staff_dump})

    record = dict(fetched_data[0])
    if user_alias.strip().lower() != record.get("emp_alias", "").lower():
        staff_dump = fetch_all_staff()
        return jsonify({"status": "success", "users": staff_dump})

    return jsonify({"status": "success", "user": record})


@app.route("/ping", methods=["POST"])
def ping():
    data = request.get_json(silent=True) or {}
    host = data.get("host", "")

    if platform.system() == "Windows":
        cmd = f"ping -n 1 {host}"
    else:
        cmd = f"ping -c 1 {host}"

    try:
        with os.popen(cmd) as proc:
            output = proc.read()
    except OSError as exc:
        output = str(exc)

    return jsonify({"output": output})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
