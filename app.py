from flask import Flask, request, jsonify
from collections import deque
import time
import requests

app = Flask(__name__)

command_queue = deque()
active_command = {"command": "OFF", "duration": 0}
cycle_ready = True

processed_payments = set()  # prevent duplicates

machine_state = {
    "status": "IDLE",
    "last_seen": time.time()
}

# ================= WHATSAPP =================
def send_whatsapp(msg, phone="91XXXXXXXXXX"):
    try:
        url = "https://api.callmebot.com/whatsapp.php"
        requests.get(url, params={
            "phone": phone,
            "text": msg,
            "apikey": "YOUR_API_KEY"
        })
    except:
        print("WhatsApp failed")

# ================= HOME =================
@app.route("/")
def home():
    return "Smart Machine Server Running"

# ================= STATUS =================
@app.route("/status")
def status():
    return jsonify({
        "queue_size": len(command_queue),
        "machine_state": machine_state,
        "active_command": active_command
    })

# ================= HEARTBEAT =================
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    machine_state["last_seen"] = time.time()
    return jsonify({"status": "ok"})

# ================= WEBHOOK =================
@app.route("/razorpay-webhook", methods=["POST"])
def webhook():
    global command_queue

    data = request.json
    print("Webhook:", data)

    try:
        payment_id = data["payload"]["payment"]["entity"]["id"]

        if payment_id in processed_payments:
            return jsonify({"status": "duplicate ignored"}), 200

        processed_payments.add(payment_id)

        amount = int(data["payload"]["payment"]["entity"]["amount"])  # paisa
    except:
        return jsonify({"status": "invalid"}), 400

    # ---------------- PRICE MAP ----------------
    if amount == 100:
        duration = 1
    elif amount == 200:
        duration = 2
    else:
        return jsonify({"status": "ignored"}), 200

    job = {
        "command": "ON",
        "duration": duration
    }

    command_queue.append(job)

    print("Added:", job)

    return jsonify({"status": "ok"}), 200

# ================= GET COMMAND =================
@app.route("/get-command")
def get_command():
    global active_command, cycle_ready, machine_state

    machine_state["status"] = "READY"

    if cycle_ready and len(command_queue) > 0:
        active_command = command_queue.popleft()
        cycle_ready = False

        machine_state["status"] = "DISPATCHED"

        print("Sent:", active_command)
        return jsonify(active_command)

    return jsonify({"command": "OFF", "duration": 0})

# ================= CYCLE COMPLETE =================
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready, machine_state

    cycle_ready = True
    machine_state["status"] = "COOLDOWN"

    send_whatsapp("✅ Washing Cycle Completed")

    return jsonify({"status": "ack"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
