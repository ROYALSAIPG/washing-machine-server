from flask import Flask, request
import requests

app = Flask(__name__)

ESP32_URL = "https://your-ngrok-url.ngrok.io"

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
            requests.get(f"{ESP32_URL}/start?duration={duration}")
            return "Machine Started", 200
        except:
            return "ESP32 Error", 500

    return "OK", 200