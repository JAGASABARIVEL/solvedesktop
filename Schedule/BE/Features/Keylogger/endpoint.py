import json
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_cors import cross_origin

from database_schema import User, KeyLogger


def init_endpoint(app_context, app, Session):
    with app_context:
        # Endpoints
        @app.route('/keylogger/ping', methods=['GET'])
        @cross_origin()
        def ping_keylogger_service():
            return jsonify({"message": "Keyloger service is alive"}), 200

        @app.route('/keylogger/<uuid>', methods=['GET'])
        @cross_origin()
        def get_user_from_uuid(uuid):
            with Session() as session:
                user = session.query(User).filter_by(uuid=uuid).first()
                if user:
                    return jsonify({"emp_id": user.id}), 200
                return jsonify({"error": "No user for the UUID"})

        @app.route('/keylogger', methods=['POST'])
        @cross_origin()
        def add_record():
            data = request.json
            uuid = data.get('uuid')
            if not uuid:
                return jsonify({"message": "MAC not provided"}), 400
            date = data.get('date')
            app_details = data.get('app_details')
            if app_details:
                print("Recived app_details ", app_details)
                app_details = json.dumps(app_details)
                print("Recived app_details after dumping ", app_details)
            idle_time = data.get('idle_time')
            with Session() as session:
                user = session.query(User).filter_by(uuid=uuid).first()
                if not user:
                    return jsonify({"error": "User is not logged into any of the system"}), 400
                organization_id = user.organization_id
                emp_id = user.id
                key_logger_data = session.query(KeyLogger).filter_by(
                    organization_id=organization_id,
                    emp_id=emp_id,
                    date=date
                ).first()
                if not key_logger_data:
                    print("No existing record - Creating")
                    key_logger_data = KeyLogger(
                        organization_id=organization_id,
                        emp_id=emp_id,
                        date=date,
                        app_details=app_details,
                        idle_time=idle_time
                    )
                    session.add(key_logger_data)
                    session.commit()
                else:
                    print("Alredy existing record - Updating")
                    key_logger_data.app_details = app_details
                    key_logger_data.idle_time = idle_time
                    session.commit()
            return jsonify({"message": "Keylogger log added"}), 201

        @app.route('/keylogger', methods=['GET'])
        @cross_origin()
        def get_records():
            organization_id = request.args.get('organization_id')
            emp_id = request.args.get('emp_id')
            date = request.args.get('date')
            if not emp_id or not organization_id:
                return jsonify({"message": "Emp Id or Org Id is not provided"}), 400
            with Session() as session:
                key_logger_data = session.query(KeyLogger).filter_by(organization_id=organization_id, emp_id=emp_id)
                if date:
                    key_logger_data.filter_by(date=date)
                key_logger_data = key_logger_data.all()
                if key_logger_data:
                    response = {}
                    # Its safe to do since we always query specific to employee and hence any index would point to a requested emploee record.
                    emp_name = session.query(User).filter_by(id=key_logger_data[0].emp_id).first()
                    for emp_key_logger_data in key_logger_data:
                        app_details = json.loads(emp_key_logger_data.app_details)
                        em_data = {
                            emp_key_logger_data.date: {
                                "app_log": app_details,
                                "total_idle_time": emp_key_logger_data.idle_time
                            }
                        }
                        response.update(em_data)
                    return jsonify({emp_name.name: response}), 200
            # No keylogger record for the employee
            return jsonify({})
