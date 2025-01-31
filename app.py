

import os
import json
import traceback
import logging
import time
from threading import Thread

from flask import Flask, request, jsonify
from confluent_kafka import Producer, KafkaError

app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

registered_phone_number_last_sent_schedule = {}
registered_phone_number_last_sent_conversation = {}

registered_phone_number_last_received = {}

# Kafka Configuration
TOPIC = 'whatsapp'

def read_config():
    """
    Reads the client configuration from kafka.config
    and returns it as a key-value dictionary.
    """
    config = {}
    with open("kafka.config") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                parameter, value = line.split('=', 1)
                config[parameter.strip()] = value.strip()
    return config

producer_config = read_config()
producer_config["sasl.username"] = os.getenv("kf_username")
producer_config["sasl.password"] = os.getenv("kf_password")

# Replace with your actual tokens
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialize Kafka Producer
producer = Producer(producer_config)

time.sleep(5)
print("Producer is ready to produce")

def flush_kafka_messages_consistently():
    while True:
        producer.flush()
        time.sleep(2)

def start_background_tasks():
    flush_thread = Thread(target=flush_kafka_messages_consistently, daemon=True)
    flush_thread.start()

def delivery_report(err, msg):
    """
    Callback for delivery reports. Logs the delivery result.
    """
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def publish_message(topic, msg):
    """
    Publishes a message to Kafka asynchronously.
    """
    try:
        producer.produce(
            topic,
            value=json.dumps(msg),
            callback=delivery_report
        )
        print("Producer produced message")
    except KafkaError as e:
        logger.error(f"Failed to produce message: {e}")

def send_msg_from_org(phone_number_id, recipient_id, message_id, message_status, error_details, msg_from_type):
    try:
        message = {
            "phone_number_id": phone_number_id,
            "recipient_id": recipient_id,
            "message_id": message_id,
            "message_status": message_status,
            "error_details": error_details,
            "msg_from_type": msg_from_type
        }
        publish_message(TOPIC, message)
    except Exception as e:
        logger.error(f"Error sending message: {e}")

def send_msg_from_customer(phone_number_id, from_user, msg, msg_type, msg_from_type):
    """
    Formats and publishes a message to Kafka.
    """
    try:
        if msg_type == "text":
            message = {
                "recipient_id": from_user,
                "message_body": msg,
                "phone_number_id": phone_number_id,
                "msg_from_type": msg_from_type
            }
        publish_message(TOPIC, message)
    except Exception as e:
        logger.error(f"Error sending message: {e}")

@app.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    Handles WhatsApp webhook events.
    """
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return challenge, 200
        else:
            logger.warning("Webhook verification failed")
            return "Forbidden", 403

    elif request.method == 'POST':
        try:
            data = request.get_json()
            logger.info(f"Received data: {data}")
            value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
            phone_number_id = value.get('metadata', {}).get('phone_number_id')
            #registered_phone_number_last_sent_schedule.setdefault(phone_number_id, {})
            if value.get('statuses'):
                recipient_id = value['statuses'][0].get('recipient_id')
                status = value['statuses'][0].get('status')

                for status in value['statuses']:
                    message_id = status.get("id")
                    message_status = status.get("status")
                    recipient_id = status.get("recipient_id")
                    error_details = None
                    if message_status == 'failed':
                        error_details = status.get('errors', [{}])
                    #TODO: This needs more efficient way of tracking the message status like conversation which uses notification based status delivery.
                    # For schedule
                    #registered_phone_number_last_sent_schedule[phone_number_id].setdefault(recipient_id, {}).update(
                    #    {
                    #        message_id: {    
                    #            "status": message_status,
                    #            "error_details": error_details
                    #        }
                    #    }
                    #)
                    send_msg_from_org(phone_number_id=phone_number_id, recipient_id=recipient_id, message_id=message_id, message_status=message_status,error_details=error_details, msg_from_type="ORG")
                logger.info(f"Status update: {status}, Error: {error_details}")
            elif value.get('messages'):
                messages = value['messages']
                for message in messages:
                    recipient_id = message.get('from')
                    if message.get('type') == 'text':
                        text_message = message['text']['body']
                        logger.info(f"Received text message from {recipient_id}: {text_message}")
                        send_msg_from_customer(phone_number_id=phone_number_id, from_user=recipient_id, msg=text_message, msg_type="text", msg_from_type="CUSTOMER")
            return jsonify({"status": "success"}), 200
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            logger.debug(traceback.format_exc())
            return jsonify({"status": "error", "message": str(e)}), 400

#@app.route('/schedule/notifications/<phone_number_id>/<recipient_phone_number>/<messageid>', methods=['GET'])
#def get_last_schedule_message_status_details_from_recipient_number(phone_number_id, recipient_phone_number, messageid):
#    response = registered_phone_number_last_sent_schedule.get(phone_number_id, {}).get(recipient_phone_number, {}).get(messageid, {"status": "unknown"})
#    return jsonify({recipient_phone_number: response})

start_background_tasks()

if __name__ == '__main__':
    app.run()
