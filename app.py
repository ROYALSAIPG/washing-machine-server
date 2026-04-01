from flask import Flask, request, jsonify
from collections import deque
import time
import requests

app = Flask(__name__)

# ================= QUEUE =================
queue = deque()
active_job = None
processed_payments = set()

# ================= MACHINE STATE =================
machine = {
    "status": "IDLE",
    "last_seen": time.time(),
    "running": False
}

# ================= WHATSAPP =================
def whatsapp(msg, phone="919226424495"):
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
    return "🚀 Smart Machine v2 Running"

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    return jsonify({
        "queue_size": len(queue),
        "active_job": active_job,
        "machine": machine
    })

# ================= HEARTBEAT =================
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    machine["last_seen"] = time.time()
    machine["status"] = "ONLINE"
    return jsonify({"status": "ok"})

# ================= RAZORPAY WEBHOOK =================
@app.route("/razorpay-webhook", methods=["POST"])
def webhook():
    global queue

    data = request.json
    print("WEBHOOK:", data)

    try:
        payment = data["payload"]["payment"]["entity"]
        payment_id = payment["id"]
        amount = int(payment["amount"])

        if payment_id in processed_payments:
            return jsonify({"status": "duplicate"}), 200

        processed_payments.add(payment_id)

    except:
        return jsonify({"status": "invalid"}), 400

    # ================= PRICE MAP =================
    if amount == 100:
        duration = 1
    elif amount == 200:
        duration = 2
    else:
        return jsonify({"status": "ignored"}), 200

    job = {
        "id": payment_id,
        "command": "ON",
        "duration": duration,
        "time": time.time()
    }

    queue.append(job)

    print("QUEUE UPDATED:", list(queue))

    whatsapp(f"💳 Payment received ₹{amount/100} - Job added")

    return jsonify({"status": "ok"}), 200

# ================= GET COMMAND (ESP32) =================
@app.route("/get-command")
def get_command():
    global active_job

    # offline detection
    if time.time() - machine["last_seen"] > 60:
        machine["status"] = "OFFLINE"

    if queue:
        active_job = queue.popleft()

        machine["status"] = "RUNNING"
        machine["running"] = True

        print("SENT TO ESP32:", active_job)

        whatsapp(f"🚀 Machine STARTED for {active_job['duration']} min")

        return jsonify(active_job)

    return jsonify({"command": "OFF", "duration": 0})

# ================= CYCLE COMPLETE =================
@app.route("/cycle-complete", methods=["POST"])
def complete():
    global active_job

    machine["status"] = "IDLE"
    machine["running"] = False

    print("CYCLE COMPLETE")

    whatsapp("✅ Machine Cycle Completed")

    active_job = None

    return jsonify({"status": "ack"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
