from datetime import datetime
from flask import request, jsonify
from database_schema import IncomingMessage, MessageResponseLog

def init_endpoint(app_context, app, Session):
    with app_context:
        # Endpoints
        @app.route('/messages/ping', methods=['GET'])
        def ping_message_service():
            return jsonify({"message": "Message service is alive"}), 200

        @app.route('/messages/incoming', methods=['GET'])
        def get_incoming_messages():
            organization_id = request.args.get('organization_id')
            messages = IncomingMessage.query.filter_by(organization_id=organization_id, status='unread').all()
            return jsonify([{
                'id': msg.id,
                'contact_id': msg.contact_id,
                'message_body': msg.message_body,
                'received_time': msg.received_time
            } for msg in messages])
        
        @app.route('/messages/respond', methods=['POST'])
        def respond_to_message():
            data = request.json
            incoming_message_id = data.get('incoming_message_id')
            user_id = data.get('user_id')
            response_message = data.get('response_message')
            with Session() as session:
                incoming_message = session.query(IncomingMessage).get(incoming_message_id).first()
                if incoming_message:
                    # Log the response
                    response_log = MessageResponseLog(
                        incoming_message_id=incoming_message_id,
                        organization_id=incoming_message.organization_id,
                        user_id=user_id,
                        response_message=response_message,
                        response_time=datetime.utcnow()
                    )
                    # TODO: Update the incoming message status by confirming from webhook to ensure its not failed
                    incoming_message.status = 'responded'
                    session.add(response_log)
                    session.commit()
                    return jsonify({'status': 'success', 'message': 'Response logged successfully'}), 200
                return jsonify({'status': 'error', 'message': 'Incoming message not found'}), 404
