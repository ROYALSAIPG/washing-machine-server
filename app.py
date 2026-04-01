from flask import Flask, request, jsonify
from collections import deque

app = Flask(__name__)

command_queue = deque()
active_command = {"command": "OFF", "duration": 0}
cycle_ready = True


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Server Running"


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
    global command_queue

    data = request.json
    print("Webhook received:", data)

    event = data.get("event")

    if event in ["payment.captured", "order.paid"]:

        try:
            # Razorpay amount is in PAISA
            amount = int(data["payload"]["payment"]["entity"]["amount"])
        except:
            return jsonify({"status": "invalid payload"}), 400

        # ---------------- EXACT MATCH LOGIC ----------------
        if amount == 100:        # ₹1
            duration = 30
        elif amount == 200:     # ₹2
            duration = 60
        else:
            print("Unknown amount:", amount)
            return jsonify({"status": "ignored amount"}), 200

        command_queue.append({
            "command": "ON",
            "duration": duration
        })

        print(f"Added to queue: ₹{amount/100} → {duration} min")

    return jsonify({"status": "ok"}), 200


# ---------------- ESP32 GET COMMAND ----------------
@app.route("/get-command")
def get_command():
    global active_command, cycle_ready

    if cycle_ready and len(command_queue) > 0:
        active_command = command_queue.popleft()
        cycle_ready = False
        print("Sent to ESP32:", active_command)

    return jsonify(active_command)


# ---------------- ESP32 CYCLE COMPLETE ----------------
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready

    cycle_ready = True
    print("Cycle completed by ESP32")

    return jsonify({"status": "ack"}), 200


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run()
