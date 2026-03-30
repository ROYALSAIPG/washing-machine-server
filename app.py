from flask import Flask, request, jsonify

app = Flask(__name__)

machine_state = "OFF"
duration = 0

@app.route("/")
def home():
    return "Server Running"

@app.route("/razorpay-webhook", methods=["POST"])
def webhook():
    global machine_state, duration

    data = request.json
    print("Webhook received:", data)

    if data and data.get("event") == "payment.captured":

        amount = data["payload"]["payment"]["entity"]["amount"]

        if amount == 5000:
            duration = 30
        elif amount == 8000:
            duration = 60
        else:
            return "Invalid amount", 400

        machine_state = "ON"

    return "OK", 200


@app.route("/get-command")
def get_command():
    global machine_state, duration

    response = {
        "command": machine_state,
        "duration": duration
    }

    machine_state = "OFF"
    duration = 0

    return jsonify(response)


@app.route("/status")
def status():
    return jsonify({
        "status": machine_state,
        "duration": duration
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
