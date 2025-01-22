import json
import time

from confluent_kafka import Consumer as ConfluentConsumer, KafkaException
import socketio

from database_schema import IncomingMessage, Contact, Platform, Organization, Conversation


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
                self.sio.connect('http://localhost:5002')

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
        recipient_id = msg_data['recipient_id']
        message_body = msg_data['message_body']
        phone_number_id = msg_data['phone_number_id']
        #timestamp = msg_data['timestamp'] This is not needed since the messages would be formwarded by broker as soon as it received on whatsapp server.

        # TODO: Get the platform Id and Organization Id from phone_number_id
        organization_id = ''
        platform_id = ''

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
                conversation = Conversation(
                    organization_id=organization.id,
                    platform_id=platform.id,
                    contact_id=contact.id
                )
                session.add(conversation)
                session.commit()
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
            self.sio.emit('whatsapp_chat', incoming_message.to_dict())
            self.app.logger.info("Contact created and message logged successfully")
