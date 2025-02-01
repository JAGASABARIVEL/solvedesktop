import json
import time

from confluent_kafka import Consumer as ConfluentConsumer, KafkaException
import socketio

from database_schema import IncomingMessage, Contact, Platform, Organization, Conversation, UserMessage, User, PlatformLog

SOCKET_URL = "http://localhost:5001"

class ConsumerService:
    def __init__(self, app, topic, group_id, config, session):
        self.app = app  # For logging
        self.topic = topic
        self.group_id = group_id
        self.session = session
        # Configure the Kafka consumer
        self.consumer_config = config
        self.consumer_config['group.id'] = self.group_id
        self.consumer_config['auto.offset.reset'] = 'earliest'
        self.sio = socketio.Client()

        @self.sio.event
        def connect():
            print('Connected to SocketIO server')

        @self.sio.event
        def disconnect():
            print('Disconnected from SocketIO server')

    def run(self):
        consumer = ConfluentConsumer(self.consumer_config)

        try:
            consumer.subscribe([self.topic])

            # Connect to SocketIO server only once
            if not self.sio.connected:
                self.sio.connect(SOCKET_URL)

            while True:
                msg = consumer.poll(timeout=1.0)  # Poll for a message

                if msg is None:
                    continue  # No message; continue polling
                if msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        self.app.logger.info(f"End of partition reached: {msg.error()}")
                    else:
                        self.app.logger.error(f"Consumer error: {msg.error()}")
                    continue

                # Process the message
                try:
                    message_value = json.loads(msg.value().decode('utf-8'))
                    self.app.logger.info(f"Received message: {message_value}")
                    self.process_message(message_value)
                except Exception as e:
                    self.app.logger.error(f"Error processing message: {e}")

        finally:
            consumer.close()

    def process_message(self, message):
        msg_data = message

        if msg_data["msg_from_type"] == "CUSTOMER":
            recipient_id = msg_data['recipient_id']
            message_body = msg_data['message_body']
            phone_number_id = msg_data['phone_number_id']
            #timestamp = msg_data['timestamp'] This is not needed since the messages would be formwarded by broker as soon as it received on whatsapp server.
            # TODO: Get the platform Id and Organization Id from phone_number_id
            conversation_id = None
            robo_user = None
            # Check or create contact and log message in the database
            with self.session() as session:
                platform = session.query(Platform).filter_by(login_id=phone_number_id).first()
                organization = session.query(Organization).filter_by(owner_id=platform.owner_id).first()
                contact = session.query(Contact).filter_by(phone=recipient_id).first()
                if not contact:
                    self.app.logger.info("Contact not found, creating new contact")
                    contact = Contact(
                        name='',
                        phone=recipient_id,
                        organization_id=organization.id,
                        created_by=organization.owner_id
                    )
                    session.add(contact)
                    session.flush()
                self.app.logger.info("Contact found / generated")
                conversation = session.query(Conversation).filter_by(
                    organization_id=organization.id,
                    platform_id=platform.id,
                    contact_id=contact.id
                ).filter(Conversation.status.in_(['new', 'active'])).first()
                if not conversation:
                    # Look up the organization to get its robo_name (or use conversation.open_by)
                    #robo_name = organization.robo_name
                    #robo_user = session.query(User).filter_by(name=robo_name, organization_id=organization.id).first()
                    conversation = Conversation(
                        organization_id=organization.id,
                        platform_id=platform.id,
                        contact_id=contact.id#,
                        #assigned_user_id=robo_user.id,
                        #status='active'
                    )
                    session.add(conversation)
                    session.commit()
                    #conversation_id = conversation.id
                incoming_message = IncomingMessage(
                    conversation_id=conversation.id,
                    contact_id=contact.id,
                    organization_id=organization.id,
                    platform_id=platform.id,
                    message_body=message_body,
                )
                session.add(incoming_message)
                session.commit()
                # Emit the message
                to_be_emit = incoming_message.to_dict()
                to_be_emit.update({"msg_from_type":"CUSTOMER"})
                self.sio.emit('whatsapp_chat', to_be_emit)
                self.app.logger.info("Contact created and message logged successfully")
            # Dont want to hold the session longer by keeping it inside since robo response may take time
            # once it is integrated with AI endpoint
            #if robo_user:
            #    send_auto_response(message_body, conversation_id)
        elif msg_data["msg_from_type"] == "ORG":
            phone_number_id = msg_data["phone_number_id"]
            message_id = msg_data["message_id"]
            message_status = msg_data["message_status"]
            recipient_id = msg_data['recipient_id']
            error_details = msg_data["error_details"]
            
            with self.session() as session:
                user_message = session.query(UserMessage).filter_by(messageid=message_id).first()
                robo_name = session.query(Organization).filter_by(id=user_message.organization_id).first().robo_name
                robo_user_id = session.query(User).filter_by(name=robo_name).first().id
                user_message.status = message_status
                session.commit()
                if error_details:
                    error_details = json.dumps(error_details)
                    self.app.logger.info("Error details for message id %s is %s", message_id, error_details)
                    user_message.status_details = error_details
                    session.commit()
                    if robo_user_id == user_message.user_id:
                        platform_log_msg = json.dumps({recipient_id: {"messageid": message_id, "Error": error_details}})
                        # Update platform logs since we know that its schedule failed which would sent as ROBO user.
                        platform_log = session.query(PlatformLog).filter_by(messageid=message_id).first()
                        platform_log.status = "Error"
                        platform_log.log_message = platform_log_msg
                        session.commit()
                # Update the status after checking the webhook notification
                session.query(IncomingMessage).filter_by(conversation_id=user_message.conversation_id).update(
                    {"status": "responded"}
                )
                session.commit()
                # Emit the message
                self.sio.emit('whatsapp_chat', {
                    "conversation_id": user_message.conversation_id,
                    "msg_from_type": "ORG"
                })
                self.app.logger.info("Contact created and message logged successfully")

        def send_auto_response(self, conversation_id, message_body):
            """
            Generate and send an auto-response message for a conversation.
            This function would later be enhanced to integrate AI-based responses.
            """
            with self.session() as session:
                pass
                # Create a UserMessage from the auto‑bot\n    auto_msg = UserMessage(\n        conversation_id=conversation.id,\n        organization_id=conversation.organization_id,\n        platform_id=conversation.platform_id,\n        user_id=robo_user.id,  # Message sent by the auto‑bot\n        message_body=auto_response_text,\n        sent_time=datetime.utcnow(),\n        status=\"sent\"\n    )\n    db.session.add(auto_msg)\n    db.session.commit()\n\n    # Optionally update conversation status or ownership\n    conversation.status = \"active\"  # Remain active until a human takes over\n    db.session.commit()\n\n    return auto_response_text\n\n\ndef generate_autobot_response():\n    # For now, return a static response. Later, integrate AI or rule-based logic.\n    return \"This is an automated response. Please wait while a human agent takes over.\""}
                
