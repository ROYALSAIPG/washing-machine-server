from flask import Flask, request
import requests

app = Flask(__name__)

# Instead of real ESP32, simulate by printing/logging
def start_machine(duration):
    print(f"[SIMULATED ESP32] Machine started for {duration} seconds")

@app.route("/")
def home():
    return "Server Running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data and data.get("event") == "payment.captured":
        amount = data["payload"]["payment"]["entity"]["amount"]
        if amount == 1000:
            duration = 30
        elif amount == 2000:
            duration = 60
        else:
            return "Invalid amount", 400

        # Simulate sending signal to ESP32 by calling function
        start_machine(duration)

        return "Machine Started (Simulated)", 200

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
