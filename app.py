from flask import Flask, request, jsonify, render_template
from collections import deque
import time
import requests

app = Flask(__name__)

# ================= SETTINGS =================
settings = {
    "prices": {
        100: 1,
        200: 2
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
def send_whatsapp(msg):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone=919226424495&text={msg}&apikey=YOUR_API_KEY"
        requests.get(url)
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
    settings["prices"] = data.get("prices", settings["prices"])
    return jsonify({"status": "updated"})

# ================= HEARTBEAT =================
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    machine_state["last_seen"] = time.time()
    machine_state["status"] = "ONLINE"
    return jsonify({"status": "ok"})

# ================= MANUAL START =================
@app.route("/manual-start", methods=["POST"])
def manual_start():
    command_queue.append({"command": "ON", "duration": 1})
    send_whatsapp("▶️ Manual Start Triggered")
    return jsonify({"status": "started"})

# ================= MANUAL STOP =================
@app.route("/manual-stop", methods=["POST"])
def manual_stop():
    global cycle_ready
    cycle_ready = True
    send_whatsapp("⏹️ Manual Stop Triggered")
    return jsonify({"status": "stopped"})

# ================= RAZORPAY =================
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
        return jsonify({"status": "ignored"})

    command_queue.append({"command": "ON", "duration": duration})

    send_whatsapp(f"✅ Payment Received ₹{amount/100}")

    return jsonify({"status": "ok"})

# ================= GET COMMAND =================
@app.route("/get-command")
def get_command():
    global active_command, cycle_ready, command_start_time

    if not cycle_ready:
        if time.time() - command_start_time > TIMEOUT:
            cycle_ready = True

    if cycle_ready and len(command_queue) > 0:
        active_command = command_queue.popleft()
        cycle_ready = False
        command_start_time = time.time()

        send_whatsapp(f"▶️ Machine Started for {active_command['duration']} min")

        return jsonify(active_command)

    return jsonify({"command": "OFF", "duration": 0})

# ================= COMPLETE =================
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready, active_command

    cycle_ready = True
    active_command = {"command": "OFF", "duration": 0}

    send_whatsapp("⏹️ Cycle Completed")

    return jsonify({"status": "ack"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
