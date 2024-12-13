import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace 'your_verify_token' with your actual verify token
# Load environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # Retrieve VERIFY_TOKEN
SECRET_KEY = os.getenv("SECRET_KEY")      # Retrieve SECRET_KEY

registered_phone_number_last_sent = {}
registered_phone_number_last_received = {}

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
                recipient_id = value.get('messages')[0].get('from')
                if value.get('messages')[0].get('type') == 'text':
                    message = value.get('messages')[0].get('text').get('body')
                    timestamp = value.get('messages')[0].get('timestamp')
                    registered_phone_number_last_received.setdefault(phone_number_id, {}).setdefault(recipient_id, {}).update({'received_time': timestamp, 'message': message})

            print("Received data:", notification)
            # Extract necessary information
            if data and 'messages' in data:
                messages = data['messages']
                for message in messages:
                    sender = message.get('from')  # Sender's phone number
                    message_text = message.get('text', {}).get('body')  # Message text
                    print(f"Message from {sender}: {message_text}")

                    # Process the message (e.g., respond, store in database, etc.)
            
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print("Error:", e)
            return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/schedule/notifications/<phone_number_id>', methods=['GET'])
def get_last_message_status_details_from_recipient_number(phone_number_id):
    print("Received phone number id:", registered_phone_number_last_sent)
    return jsonify(registered_phone_number_last_sent.get(phone_number_id, {}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
