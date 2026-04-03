@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    global command_queue

    print("🔥 WEBHOOK HIT")

    # SAFE PARSING (IMPORTANT FIX)
    data = request.get_json(silent=True)

    if not data:
        data = request.form.to_dict()

    print("PAYLOAD:", data)

    try:
        payment = data["payload"]["payment"]["entity"]

        payment_id = payment.get("id")
        amount = int(payment.get("amount", 0))

        print("PAYMENT ID:", payment_id)
        print("AMOUNT:", amount)

        if payment_id in processed_payments:
            return jsonify({"status": "duplicate"})

        processed_payments.add(payment_id)

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return jsonify({"status": "invalid"}), 400

    duration = settings["prices"].get(amount)

    if not duration:
        print("Unknown amount:", amount)
        return jsonify({"status": "ignored"})

    command_queue.append({"command": "ON", "duration": duration})

    # 🔥 WhatsApp message (FIXED FLOW)
    send_whatsapp(f"✅ Payment Received ₹{amount/100}")

    print("QUEUE:", list(command_queue))

    return jsonify({"status": "ok"})
