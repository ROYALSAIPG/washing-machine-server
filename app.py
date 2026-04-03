@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    print("🔥 WEBHOOK HIT")

    # =========================
    # 1. SAFE PARSING
    # =========================
    data = request.get_json(silent=True)

    if not data:
        try:
            data = request.form.to_dict()
        except Exception:
            return jsonify({"status": "bad_request"}), 400

    print("PAYLOAD:", data)

    # =========================
    # 2. EXTRACT PAYMENT
    # =========================
    try:
        payment = data["payload"]["payment"]["entity"]

        payment_id = payment.get("id")
        amount = int(payment.get("amount", 0))

        print("PAYMENT ID:", payment_id)
        print("AMOUNT (paise):", amount)

    except Exception as e:
        print("❌ WEBHOOK PARSE ERROR:", e)
        return jsonify({"status": "invalid"}), 400

    # =========================
    # 3. DUPLICATE CHECK (DB SAFE)
    # =========================
    if db_payment_exists(payment_id):   # 🔥 REPLACE GLOBAL SET
        print("⚠️ Duplicate payment ignored")
        return jsonify({"status": "duplicate"})

    # Save payment first (IMPORTANT)
    save_payment(payment_id, amount)

    # =========================
    # 4. MAP AMOUNT → DURATION
    # =========================
    duration = settings["prices"].get(amount)

    if not duration:
        print("❌ Unknown amount:", amount)
        return jsonify({"status": "ignored"})

    # =========================
    # 5. STORE COMMAND IN DB (CRITICAL FIX)
    # =========================
    command_id = create_command(
        payment_id=payment_id,
        command="ON",
        duration=duration
    )

    print("✅ COMMAND STORED:", command_id)

    # =========================
    # 6. ASYNC WHATSAPP (NON-BLOCKING)
    # =========================
    try:
        import threading

        threading.Thread(
            target=send_whatsapp,
            args=(f"✅ Payment Received ₹{amount/100}",)
        ).start()

    except Exception as e:
        print("⚠️ WhatsApp error:", e)

    # =========================
    # 7. RESPONSE FAST (VERY IMPORTANT)
    # =========================
    return jsonify({
        "status": "ok",
        "command_id": command_id
    })
