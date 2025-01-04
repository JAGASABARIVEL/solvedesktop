
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_socketio import SocketIO, emit

# Configure logging
log_file = "socketio-server.log"
max_log_size = 100 * 1024 * 1024  # 100 MB
backup_count = 5  # Keep the last 5 log files

handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
handler.setLevel(logging.INFO)  # Set logging level
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# Models
app = None

def create_app():
    global app
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for file uploads

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    with app.app_context() as app_context:
        socketio = SocketIO(app, cors_allowed_origins="*")

        # Handle connection and disconnection events
        @socketio.event
        def connect():
            print("Client connected")
    
        @socketio.event
        def disconnect():
            print("Client disconnected")

        @socketio.on("whatsapp_chat")
        def handle_message(data):
            print(f"Message received: {data}")
            emit('message', data, broadcast=True)  # Broadcast message to all connected clients

    return app, socketio
