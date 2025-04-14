from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

# Twilio account credentials - you need to sign up at https://www.twilio.com

@app.route("/webhook", methods=['POST'])
def receive_whatsapp_message():
    """
    Function to listen to WhatsApp messages via Twilio.
    This sets up a webhook endpoint that Twilio can POST to when a message is received.
    """
    # Get the message content
    incoming_msg = request.values.get('Body', '').strip()
    # Get the sender's WhatsApp number
    sender = request.values.get('From', '')
    
    print(f"Received message: '{incoming_msg}' from {sender}")
    
    # Create a response
    resp = MessagingResponse()
    
    # You can customize the response based on the incoming message
    resp.message(f"Thank you for your message: '{incoming_msg}'")
    
    return str(resp)

if __name__ == "__main__":
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)