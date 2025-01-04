"""

import json
import time

from kafka import KafkaConsumer
import socketio

from database_schema import IncomingMessage, Contact, Platform, Organization, Conversation


class Consumer():
    def __init__(self, app, topic, group_id, bootstrap_servers, session):
        self.app = app # For log
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.session = session
        self.sio = socketio.Client()

        @self.sio.event
        def connect():
            print('Connected to SocketIO server')

        @self.sio.event
        def disconnect():
            print('Disconnected from SocketIO server')

    def run(self):
        consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        # Connect to SocketIO server only once
        if not self.sio.connected:
            self.sio.connect('http://localhost:5002')
        for message in consumer:
            self.app.logger.info(f"Received message: {message.value}")
            self.process_message(message.value)

    
    
    def process_message(self, message):
        msg_data = message
        recipient_id = msg_data['recipient_id']
        message_body = msg_data['message_body']
        phone_number_id = msg_data['phone_number_id']
        timestamp = msg_data['timestamp']
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
                organization_id = organization.id,
                platform_id=platform.id,
                message_body=message_body,
            )
            session.add(incoming_message)
            session.commit()
            # Emit the message
            self.sio.emit('whatsapp_chat', incoming_message.to_dict())
            self.app.logger.info("Contact created and message logged successfully")
"""