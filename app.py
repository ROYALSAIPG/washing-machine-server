from flask import Flask, request, jsonify
from collections import deque

app = Flask(__name__)

# Queue for commands
command_queue = deque()

# Current active command (sent to ESP32)
active_command = {"command": "OFF", "duration": 0}

# Flag: ESP32 finished last cycle
cycle_ready = True


# ---------------- STATUS ----------------
@app.route("/status")
def status():
    return jsonify({
        "queue_size": len(command_queue),
        "active_command": active_command,
        "cycle_ready": cycle_ready
    })


# ---------------- RAZORPAY WEBHOOK ----------------
@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    global command_queue, cycle_ready

    data = request.json
    print("Webhook received:", data)

    # Example: payment success
    event = data.get("event")

    if event == "payment.captured" or event == "order.paid":

        # Example logic (you can change this)
        amount = data["payload"]["payment"]["entity"]["amount"] / 100

        # Decide duration
        if amount >= 60:
            duration = 60
        else:
            duration = 30

        command_queue.append({
            "command": "ON",
            "duration": duration
        })

        print("Added to queue:", duration)

    return jsonify({"status": "ok"}), 200


# ---------------- ESP32 POLLING ----------------
@app.route("/get-command")
def get_command():
    global active_command, command_queue, cycle_ready

    # If queue has new command and ESP32 is ready
    if cycle_ready and len(command_queue) > 0:

        active_command = command_queue.popleft()
        cycle_ready = False   # lock until cycle complete

        print("Sent to ESP32:", active_command)

    return jsonify(active_command)


# ---------------- ESP32 COMPLETION SIGNAL ----------------
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready

    cycle_ready = True
    print("Cycle completed by ESP32")

    return jsonify({"status": "ack"})


# ---------------- TEST ----------------
@app.route("/")
def home():
    return "Server Running"


if __name__ == "__main__":
    app.run()
