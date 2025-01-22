import os
import json
import traceback

from flask import Flask, request, jsonify
from confluent_kafka import Producer, KafkaError

app = Flask(__name__)

# Kafka Configuration
TOPIC = 'whatsapp'

def read_config():
  # reads the client configuration from client.properties
  # and returns it as a key-value map
  config = {}
  with open("kafka.config") as fh:
    for line in fh:
      line = line.strip()
      if len(line) != 0 and line[0] != "#":
        parameter, value = line.strip().split('=', 1)
        config[parameter] = value.strip()
  return config

producer_config = read_config()
producer_config["sasl.username"] = os.getenv("kf_username")
producer_config["sasl.password"] = os.getenv("kf_password")

# Replace 'your_verify_token' with your actual verify token
# Load environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # Retrieve VERIFY_TOKEN
SECRET_KEY = os.getenv("SECRET_KEY")      # Retrieve SECRET_KEY

registered_phone_number_last_sent = {}
registered_phone_number_last_received = {}


producer = Producer(producer_config)
def delivery_report(err, msg):
    """
    Callback for delivery reports.
    Called once for each message produced to indicate delivery result.
    """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def publish_message(topic, msg):
    try:
        # Produce a message asynchronously
        producer.produce(
            topic,
            value=json.dumps(msg),
            callback=delivery_report  # Attach the delivery callback
        )
        # Ensure messages are flushed to Kafka
        producer.flush()
    except KafkaError as e:
        print(f"Failed to produce message: {e}")

def send_msg(phone_number_id, from_user, msg, msg_type):
    try:
        data = request.json
        if msg_type == "text":
            message = {
                "recipient_id": from_user,
                "message_body": msg,
                "phone_number_id": phone_number_id
            }
        publish_message(TOPIC, message)
    except Exception as e:
        raise Exception("Failed to publish message to broker") from e

@app.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    recipient_id = None
    status = None
    error_details = None
    if request.method == 'GET':
        # Verification request from WhatsApp
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            # Validating the webhook
            print("Webhook verified successfully")
            return challenge, 200
        else:
            # Verification failed
            print("Webhook verification failed")
            return "Forbidden", 403

    elif request.method == 'POST':
        # Handle incoming messages
        try:
            data = request.get_json()
            notification = data
            value = notification.get('entry')[0].get('changes')[0].get('value')
            phone_number_id = value.get('metadata').get('phone_number_id')
            if value.get('statuses'):
                recipient_id = value.get('statuses')[0].get('recipient_id')
                status = value.get('statuses')[0].get('status') 
                if status in ['failed']:
                    error_details = value.get('statuses')[0].get('errors')[0].get('error_data').get('details')
                registered_phone_number_last_sent.setdefault(phone_number_id, {}).setdefault(recipient_id, {}).update({'status': status})
                registered_phone_number_last_sent.setdefault(phone_number_id, {}).setdefault(recipient_id, {}).update({'error_details': error_details})
            elif value.get('messages'):
                messages = value.get('messages')
                for message in messages:
                    recipient_id = message.get('from')
                    if message.get('type') == 'text':
                        message = message.get('text').get('body')
                        timestamp = message.get('timestamp')
                        registered_phone_number_last_received.setdefault(phone_number_id, {}).setdefault(recipient_id, {}).update({'received_time': timestamp, 'message': message})

            print("Received data:", notification)
            # Extract necessary information
            if notification and 'messages' in value:
                messages = value.get('messages')
                for message in messages:
                    sender = message.get('from')  # Sender's phone number
                    message_text = message.get('text', {}).get('body')  # Message text
                    print(f"Message from {sender}: {message_text}")
                    send_msg(phone_number_id=phone_number_id, from_user=sender, msg=message_text, msg_type="text")
                    # Process the message (e.g., respond, store in database, etc.)
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print("Error:", e)
            print(traceback.format_exc())
            return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/schedule/notifications/<phone_number_id>', methods=['GET'])
def get_last_message_status_details_from_recipient_number(phone_number_id):
    print("Received phone number id:", registered_phone_number_last_sent)
    return jsonify(registered_phone_number_last_sent.get(phone_number_id, {}))





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
