import sqlite3
@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    print("🔥 WEBHOOK HIT")

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": "bad_request"}), 400

    try:
        payment = data["payload"]["payment"]["entity"]

        payment_id = payment.get("id")
        amount = int(payment.get("amount", 0))

    except Exception as e:
        print("❌ PARSE ERROR:", e)
        return jsonify({"status": "invalid"}), 400

    # ================= DUPLICATE CHECK =================
    if db_payment_exists(payment_id):
        return jsonify({"status": "duplicate"})

    save_payment(payment_id, amount)

    # ================= AMOUNT MAP =================
    duration = settings["prices"].get(amount)

    if not duration:
        return jsonify({"status": "ignored"})

    # ================= CREATE COMMAND =================
    command_id = create_command(
        payment_id=payment_id,
        command="ON",
        duration=duration
    )

    # 🔥 IMPORTANT: mark as SENT immediately (prevents duplicate fetching confusion)
    update_command_status(command_id, "SENT")

    print("✅ COMMAND CREATED:", command_id)

    return jsonify({
        "status": "ok",
        "command_id": command_id,
        "command": "ON",
        "duration": duration
    })
