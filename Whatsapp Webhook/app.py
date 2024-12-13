import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace 'your_verify_token' with your actual verify token
# Load environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # Retrieve VERIFY_TOKEN
SECRET_KEY = os.getenv("SECRET_KEY")      # Retrieve SECRET_KEY

@app.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
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
            print("Received data:", data)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
