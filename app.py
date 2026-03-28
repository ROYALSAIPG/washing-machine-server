from flask import Flask, request
import requests

app = Flask(__name__)

# Use a mock ESP32 URL for testing
ESP32_URL = "http://127.0.0.1:5000/start"  # We’ll create this route next

@app.route("/")
def home():
    return "Server Running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data.get("event") == "payment.captured":
        amount = data["payload"]["payment"]["entity"]["amount"]

        if amount == 5000:
            duration = 30
        elif amount == 8000:
            duration = 60
        else:
            return "Invalid amount", 400

        try:
            # Call mock ESP32
            requests.get(f"{ESP32_URL}?duration={duration}")
            return f"Machine Started for {duration} seconds (Mock)", 200
        except Exception as e:
            print(e)
            return "ESP32 Error", 500

    return "OK", 200

# Mock ESP32 endpoint
@app.route("/start")
def start_machine():
    duration = request.args.get("duration")
    print(f"[MOCK ESP32] Machine would run for {duration} seconds")
    return f"Machine started for {duration} seconds (Mock)"
    
if __name__ == "__main__":
    app.run(debug=True)
