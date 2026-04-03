from flask import Flask, request, jsonify, render_template
from collections import deque
import time
import requests
import os

app = Flask(__name__)

# ================= SETTINGS =================
settings = {
    "prices": {
        100: 1,   # ₹1 → 1 min
        200: 2    # ₹2 → 2 min
    }
}

# ================= STATE =================
command_queue = deque()
active_command = {"command": "OFF", "duration": 0}
cycle_ready = True
command_start_time = 0

processed_payments = set()

machine_state = {
    "status": "IDLE",
    "last_seen": time.time()
}

TIMEOUT = 120

# ================= WHATSAPP =================
ACCESS_TOKEN = "EAAlR6bDuHQQBRCixbyMFXrGXBh5tx9MALiBaQ1O8BLZA7FHtU1yGYL0un6PYO1NeJZBtpSqGZCV1ezIpxa1nJcpo8DRBhXE00CXGzWeEElN4WrMuG43IvFjRF9wBqI82bUFbTAPtZCIZAeAqBZCJEw09BpiXwalaIUOo04p4ffApsFtboDtHWDmVIJkk8imnqBQAZDZD"
PHONE_NUMBER_ID = "1026438257222002"
TO_NUMBER = "919226424495"

def send_whatsapp(msg):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": TO_NUMBER,
        "type": "text",
        "text": {"body": msg}
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        print("WhatsApp Status:", response.status_code)
        print("WhatsApp Response:", response.text)

    except Exception as e:
        print("WhatsApp error:", e)

# ================= HOME =================
@app.route("/")
def home():
    return "Smart Machine Server Running"

# ================= ADMIN =================
@app.route("/admin")
def admin():
    return render_template("admin.html")

# ================= STATUS =================
@app.route("/status")
def status():
    return jsonify({
        "queue_size": len(command_queue),
        "active_command": active_command,
        "cycle_ready": cycle_ready,
        "machine_state": machine_state
    })

# ================= GET SETTINGS =================
@app.route("/get-settings")
def get_settings():
    return jsonify(settings)

# ================= UPDATE SETTINGS =================
@app.route("/update-settings", methods=["POST"])
def update_settings():
    global settings

    data = request.json
    new_prices = data.get("prices", {})

    fixed_prices = {}
    for k, v in new_prices.items():
        try:
            fixed_prices[int(k)] = int(v)
        except:
            pass

    settings["prices"] = fixed_prices

    print("UPDATED SETTINGS:", settings)

    return jsonify({"status": "updated", "settings": settings})

# ================= HEARTBEAT =================
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    machine_state["last_seen"] = time.time()
    machine_state["status"] = "ONLINE"
    return jsonify({"status": "ok"})

# ================= MANUAL START =================
@app.route("/manual-start", methods=["POST"])
def manual_start():
    data = request.json
    duration = int(data.get("duration", 1))  # default 1 min

    command_queue.append({"command": "ON", "duration": duration})

    send_whatsapp(f"▶️ Manual Start for {duration} min")

    return jsonify({"status": "started", "duration": duration})

# ================= MANUAL STOP =================
@app.route("/manual-stop", methods=["POST"])
def manual_stop():
    global cycle_ready
    cycle_ready = True
    send_whatsapp("⏹️ Manual Stop Triggered")
    return jsonify({"status": "stopped"})

# ================= RAZORPAY WEBHOOK =================
@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    global command_queue

    data = request.json

    try:
        payment = data["payload"]["payment"]["entity"]
        payment_id = payment["id"]
        amount = int(payment["amount"])

        if payment_id in processed_payments:
            return jsonify({"status": "duplicate"})

        processed_payments.add(payment_id)

    except:
        return jsonify({"status": "invalid"}), 400

    duration = settings["prices"].get(amount)

    if not duration:
        print("Unknown amount:", amount)
        return jsonify({"status": "ignored"})

    command_queue.append({"command": "ON", "duration": duration})

    send_whatsapp(f"✅ Payment Received ₹{amount/100}")

    print("QUEUE:", list(command_queue))

    return jsonify({"status": "ok"})

# ================= GET COMMAND =================
@app.route("/get-command")
def get_command():
    global active_command, cycle_ready, command_start_time

    # Timeout safety
    if not cycle_ready:
        if time.time() - command_start_time > TIMEOUT:
            print("Timeout reset")
            cycle_ready = True

    if cycle_ready and len(command_queue) > 0:
        active_command = command_queue.popleft()
        cycle_ready = False
        command_start_time = time.time()

        machine_state["status"] = "RUNNING"

        send_whatsapp(f"▶️ Machine Started for {active_command['duration']} min")

        return jsonify(active_command)

    return jsonify({"command": "OFF", "duration": 0})

# ================= COMPLETE =================
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready, active_command

    cycle_ready = True
    active_command = {"command": "OFF", "duration": 0}

    machine_state["status"] = "COMPLETED"

    send_whatsapp("⏹️ Cycle Completed")

    print("Cycle completed")

    return jsonify({"status": "ack"})
# ================= TEST WHATSAPP (ADD THIS HERE) =================
@app.route("/test-whatsapp")
def test_whatsapp_route():
    send_whatsapp("🔥 Test message from Flask server")
    return "WhatsApp test triggered"

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render compatible
    app.run(host="0.0.0.0", port=port)
