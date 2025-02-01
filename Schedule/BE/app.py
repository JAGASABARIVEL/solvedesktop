
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS

from sqlalchemy.orm import sessionmaker

from database_schema import db as SQLalchemy

# Import Apps
from Features.Schedule import endpoint as schedule_endpoint
from Features.Messages import endpoint as message_endpoint
from Features.Keylogger import endpoint as keylogger_endpoint
from Features.Tasks import endpoint as task_endpoint


# Configure logging
log_file = "schedule-server.log"
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
db = SQLalchemy


def create_app():
    global app
    global db
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduling.db'  # Update with your DB URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for file uploads

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    with app.app_context() as app_context:
        db.init_app(app)
        db.create_all()
        CORS(app, resources={r"/*": {"origins": "*"}})
        Session = sessionmaker(bind=db.engine)
        
        print("Init message endpoint")
        message_endpoint.init_endpoint(app_context, app, Session)

        print("Init schedule endpoint")
        schedule_endpoint.init_endpoint(app_context, app, Session)

        print("Init keylogger endpoint")
        keylogger_endpoint.init_endpoint(app_context, app, Session)

        print("Init task endpoint")
        task_endpoint.init_endpoint(app_context, app, Session)

        @app.route('/ping', methods=["GET"])
        def ping_main_server():
            return jsonify({"message": "Server is alive"}), 200

    return app
