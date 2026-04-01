from flask import Flask, request, jsonify
from collections import deque
import time

app = Flask(__name__)

# ================= STATE =================
command_queue = deque()
active_command = {"command": "OFF", "duration": 0}
cycle_ready = True

processed_payments = set()

machine_state = {
    "status": "IDLE",
    "last_seen": time.time()
}

# ================= HOME =================
@app.route("/")
def home():
    return "Smart Machine Server Running"

# ================= STATUS =================
@app.route("/status")
def status():
    return jsonify({
        "queue_size": len(command_queue),
        "active_command": active_command,
        "cycle_ready": cycle_ready,
        "machine_state": machine_state
    })

# ================= HEARTBEAT =================
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    machine_state["last_seen"] = time.time()
    machine_state["status"] = "ONLINE"
    return jsonify({"status": "ok"})

# ================= RAZORPAY WEBHOOK =================
@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    global command_queue

    data = request.json
    print("Webhook received:", data)

    try:
        payment = data["payload"]["payment"]["entity"]
        payment_id = payment["id"]
        amount = int(payment["amount"])  # paisa

        # prevent duplicate payment processing
        if payment_id in processed_payments:
            return jsonify({"status": "duplicate ignored"}), 200

        processed_payments.add(payment_id)

    except:
        return jsonify({"status": "invalid payload"}), 400

    # ================= PRICE MAP =================
    if amount == 100:        # ₹1
        duration = 1
    elif amount == 200:      # ₹2
        duration = 2
    else:
        print("Unknown amount:", amount)
        return jsonify({"status": "ignored"}), 200

    job = {
        "command": "ON",
        "duration": duration
    }

    command_queue.append(job)

    print("QUEUE UPDATED:", list(command_queue))

    return jsonify({"status": "ok"}), 200

# ================= ESP32 GET COMMAND =================
@app.route("/get-command")
def get_command():
    global active_command, cycle_ready

    machine_state["status"] = "READY"

    if cycle_ready and len(command_queue) > 0:
        active_command = command_queue.popleft()
        cycle_ready = False

        machine_state["status"] = "DISPATCHED"

        print("SENT TO ESP32:", active_command)
        return jsonify(active_command)

    return jsonify({"command": "OFF", "duration": 0})

# ================= CYCLE COMPLETE =================
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready

    cycle_ready = True
    machine_state["status"] = "COOLDOWN"

    print("Cycle completed by ESP32")

    return jsonify({"status": "ack"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
