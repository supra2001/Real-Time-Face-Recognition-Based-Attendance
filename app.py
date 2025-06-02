from flask import Flask, render_template, redirect, url_for
import subprocess
import logging
import os
import webbrowser
import threading
import time
import sys

app = Flask(__name__)

# Logging setup
logging.basicConfig(filename='flask_app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

@app.route('/')
def home():
    return render_template('index.html')  # Ensure index.html exists in templates/

@app.route('/start')
def start():
    logging.info("🟢 Start Recognition button clicked")
    print("[DEBUG] Start Recognition button clicked")

    try:
        subprocess.Popen(["python", "main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        logging.error(f"Error launching recognition script: {e}")
        return f"<h3 style='color:red;'>Error starting recognition: {e}</h3>"

    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    logging.info("🟢 Streamlit dashboard requested")
    print("[DEBUG] Launching Streamlit dashboard...")

    try:
        subprocess.Popen(
            ["streamlit", "run", "attendance_dashboard.py", 
             "--browser.serverAddress=127.0.0.1", 
             "--browser.gatherUsageStats=false", 
             "--server.headless=true"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
        return "<h3>✅ Streamlit dashboard is launching...</h3><a href='/'>Go Back</a>"
    except Exception as e:
        logging.error(f"Error launching dashboard: {e}")
        return f"<h3 style='color:red;'>Error launching dashboard: {e}</h3><a href='/'>Go Back</a>"

@app.route('/about')
def about():
    return render_template('about.html')  # Ensure about.html exists in templates/

if __name__ == '__main__':
    # Prevent browser from auto-opening when launched via subprocess (e.g., from /dashboard)
    if len(sys.argv) == 1:
        def open_browser():
            webbrowser.open_new("http://127.0.0.1:5050")
        threading.Timer(1.25, open_browser).start()

    print("[DEBUG] Flask app starting and browser will open if directly launched...")
    app.run(debug=True, port=5050)
