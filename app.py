from flask import Flask, request, jsonify
from collections import deque
import time
import requests

app = Flask(__name__)

# ================= STATE =================
queue = deque()
active_job = None
processed_payments = set()

machine_state = {
    "status": "IDLE",
    "last_seen": time.time()
}

# ================= WHATSAPP =================
def send_whatsapp(msg, phone="919226424495"):
    try:
        requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={
                "phone": phone,
                "text": msg,
                "apikey": "YOUR_API_KEY"
            },
            timeout=5
        )
    except:
        print("WhatsApp failed")

# ================= HOME =================
@app.route("/")
def home():
    return "Smart Washing Machine Server Running"

# ================= STATUS =================
@app.route("/status")
def status():
    return jsonify({
        "queue_size": len(queue),
        "active_job": active_job,
        "machine_state": machine_state
    })

# ================= HEARTBEAT =================
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    machine_state["last_seen"] = time.time()
    machine_state["status"] = "ONLINE"
    return jsonify({"status": "ok"})

# ================= WEBHOOK =================
@app.route("/razorpay-webhook", methods=["POST"])
def webhook():
    global queue

    data = request.json
    print("Webhook:", data)

    try:
        payment = data["payload"]["payment"]["entity"]
        payment_id = payment["id"]
        amount = int(payment["amount"])  # paisa

        if payment_id in processed_payments:
            return jsonify({"status": "duplicate"}), 200

        processed_payments.add(payment_id)

    except:
        return jsonify({"status": "invalid"}), 400

    # ================= PRICE MAP =================
   
