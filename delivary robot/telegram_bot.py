import requests

class TelegramBot:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message):
        """Send message to Telegram chat"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram API Error: {e}")
            return False
    
    def send_pin_notification(self, username, product_name, pin_code):
        """Send PIN notification for order"""
        message = f"""
🚀 <b>New Order Received!</b>

👤 <b>Customer:</b> {username}
📦 <b>Product:</b> {product_name}
🔐 <b>PIN Code:</b> <code>{pin_code}</code>

⏰ Please deliver the item and ask customer to enter the PIN.
        """
        return self.send_message(message)
    
    def send_pin_verification(self, username, product_name, pin_code, is_correct):
        """Send PIN verification result"""
        status = "✅ CORRECT" if is_correct else "❌ WRONG"
        message = f"""
🔐 <b>PIN Verification</b>

👤 <b>Customer:</b> {username}
📦 <b>Product:</b> {product_name}
🔢 <b>PIN Attempt:</b> {pin_code}
📊 <b>Status:</b> {status}

{"🎉 Delivery completed successfully!" if is_correct else "⚠️ Please check the PIN and try again."}
        """
        return self.send_message(message)

# Initialize Telegram Bot with your credentials
# Replace with your actual bot token and chat ID
telegram_bot = TelegramBot(
    bot_token="8249485043:AAHMm0kul_8W_L--4U2SHZjaSv79fGO2-B4",
    chat_id="5119966072"
)