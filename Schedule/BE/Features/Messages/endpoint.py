from threading import Thread
from datetime import datetime
from flask import request, jsonify

from database_schema import IncomingMessage, MessageResponseLog, Conversation, User, UserMessage, Contact

from Features.Messages import Consumer

TOPIC = "whatsapp"
GRP_ID = "whatsapp-grp"
BOOTSTRAP_SERVER = "localhost:9092"


def init_endpoint(app_context, app, Session):
    with app_context:

        def start_consumer():
            Consumer(app, topic=TOPIC, group_id=GRP_ID, bootstrap_servers=BOOTSTRAP_SERVER, session=Session).run()
        # Start the consumer in a separate thread
        consumer_thread = Thread(target=start_consumer, daemon=True)
        consumer_thread.start()

        # Endpoints
        @app.route('/chat/ping', methods=['GET'])
        def ping_message_service():
            return jsonify({"message": "Message service is alive"}), 200
        
        @app.route('/chat/conversations', methods=['GET'])
        def get_unassigned_conversations():
            organization_id = request.args.get('organization_id')
            if not organization_id:
                return jsonify({'error': 'Organization ID is required'}), 400
            with Session() as session:
                conversations = session.query(Conversation).filter_by(assigned_user_id=None, organization_id=organization_id).all()
                if not conversations:
                    return jsonify([])
                
                result = []
                for conv in conversations:
                    assigned_user = session.query(User).get(conv.assigned_user_id)
                    contact = session.query(Contact).get(conv.contact_id)
                    if not assigned_user:
                        conv_data = {
                            'conversation_id': conv.id,
                            'contact': {
                                'name': contact.name,
                                'phone': contact.phone
                            },
                            'assigned': None,
                            'organization_id': conv.organization_id,
                            'status': conv.status,
                            'created_at': conv.created_at
                        }
                    else:
                        conv_data = {
                            'conversation_id': conv.id,
                            'contact': {
                                'name': contact.name,
                                'phone': contact.phone
                            },
                            'assigned': {
                                'id': assigned_user.id,
                                'name': assigned_user.name
                            },
                            'organization_id': conv.organization_id,
                            'status': conv.status,
                            'created_at': conv.created_at
                        }
                    result.append(conv_data)
                return jsonify(result)
        
        @app.route('/chat/conversations/<int:conversation_id>', methods=['GET'])
        def get_conversation(conversation_id):
            with Session() as session:
                conversation = session.query(Conversation).get(conversation_id)
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                incoming_msgs = session.query(IncomingMessage).filter_by(conversation_id=conversation_id).all()
                contact = session.query(Contact).get(conversation.contact_id)
                assignee = None
                if conversation.assigned_user_id:
                    assignee = session.query(User).get(conversation.assigned_user_id)
                incoming_messages = [
                    {
                        'id': msg.id,
                        'type': 'customer',
                        'message_body': msg.message_body,
                        'status': msg.status,
                        'received_time': msg.received_time
                    }
                    for msg in incoming_msgs
                ]
                # Fetch assigned user messages (if any table exists for user messages, example UserMessage)
                user_msgs = session.query(UserMessage).filter_by(conversation_id=conversation_id).all()
                assigned_user_messages = [
                    {
                        'id': msg.id,
                        'type': 'org',
                        'message_body': msg.message_body,
                        'status': msg.status,
                        'sent_time': msg.sent_time
                    }
                    for msg in user_msgs
                ]
                # Combine both incoming and assigned user messages and sort them by time
                combined_messages = incoming_messages + assigned_user_messages
                combined_messages.sort(key=lambda x: x['received_time'] if x['type'] == 'customer' else x['sent_time'])
                return jsonify({
                    'conversation_id': conversation.id,
                    'contact': {
                        'id': contact.id,
                        'name': contact.name,
                        'phone': contact.phone
                    },
                    'assigned': {
                        'id': assignee.id if assignee else None,
                        'name': assignee.name if assignee else None
                    },
                    'created_at': conversation.created_at,
                    'organization_id': conversation.organization_id,
                    'status': conversation.status,
                    'messages': combined_messages
                })
        
        @app.route('/chat/conversations/assign/<int:conversation_id>', methods=['POST'])
        def assign_conversation(conversation_id):
            with Session() as session:
                data = request.get_json()
                user_id = data.get('user_id')
                conversation = session.query(Conversation).get(conversation_id)
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                user = session.query(User).get(user_id)
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                conversation.assigned_user_id = user_id
                conversation.status = 'active'
                conversation.updated_at = datetime.utcnow()
                session.commit()
                return jsonify({'message': 'Conversation assigned successfully', 'conversation_id': conversation.id, 'assigned_user_id': user_id})

        @app.route('/chat/conversations/respond', methods=['POST'])
        def respond_to_message():
            data = request.json
            conversation_id = data.get('conversation_id')
            message_body = data.get('message_body')
            user_id = data.get('user_id')
            # TODO: Update the status after checking the webhook notification
            status = "sent"
            with Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                user_message = UserMessage(
                    conversation_id=conversation.id,
                    organization_id=conversation.organization_id,
                    platform_id=conversation.platform_id,
                    user_id=user_id,
                    message_body=message_body,
                    status=status
                )
                session.add(user_message)
                session.commit()
                return jsonify({'status': 'success', 'message': 'Response logged successfully'}), 200
        
        @app.route('/chat/conversations/close/<int:conversation_id>', methods=['POST'])
        def close_conversation(conversation_id):
            with Session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if not conversation:
                    return jsonify({'error': 'Conversation not found'}), 404
                conversation.status = 'closed'
                session.commit()
                return jsonify({'status': 'success', 'message': 'Conversation closed successfully'}), 200
    return app
