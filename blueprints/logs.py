from flask import Blueprint, Response, render_template
import time
from utils.logging_helper import log_data

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
def logs_page():
    return render_template('logs.html')  # Ensure 'logs.html' exists in the 'templates' folder

# Stream logs
@logs_bp.route('/logs/stream')
def stream_logs():
    def generate():
        previous_log_count = 0
        while True:
            if len(log_data) > previous_log_count:
                for log_entry in log_data[previous_log_count:]:
                    yield f"data: {log_entry}\n\n"
                previous_log_count = len(log_data)
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')
