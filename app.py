from flask import Flask, request, jsonify

app = Flask(__name__)

# Global variables
machine_state = "OFF"
duration = 0


# 🟢 Home route
@app.route("/")
def home():
    return "Server Running"


# 🔥 Razorpay Webhook (IMPORTANT)
@app.route("/razorpay-webhook", methods=["POST"])
def webhook():
    global machine_state, duration

    data = request.json

    print("🔥 WEBHOOK HIT")
    print(data)

    if data and data.get("event") == "payment.captured":

        amount = data["payload"]["payment"]["entity"]["amount"]
        print("💰 Amount:", amount)

        # ₹50 = 5000 paise
        if amount == 5000:
            duration = 30   # 30 minutes
        elif amount == 8000:
            duration = 60   # 60 minutes
        else:
            print("❌ Invalid amount")
            return "Invalid amount", 400

        machine_state = "ON"
        print("⚡ MACHINE SET TO ON")

    return "OK", 200


# 🔌 ESP32 will call this
@app.route("/get-command")
def get_command():
    global machine_state, duration

    response = {
        "command": machine_state,
        "duration": duration
    }

    print("📡 ESP32 Requested:", response)

    # Reset after sending
    machine_state = "OFF"
    duration = 0

    return jsonify(response)


# 📱 Mobile status check
@app.route("/status")
def status():
    return jsonify({
        "status": machine_state,
        "duration": duration
    })


# 🧪 Manual test (VERY IMPORTANT)
@app.route("/test-on")
def test_on():
    global machine_state, duration
    machine_state = "ON"
    duration = 30
    print("🧪 TEST MODE ON")
    return "Machine ON (Test)"


# 🚀 Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
