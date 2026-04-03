# ================= CYCLE COMPLETE =================
@app.route("/cycle-complete", methods=["POST"])
def cycle_complete():
    global cycle_ready, active_command

    cycle_ready = True
    active_command = {"command": "OFF", "duration": 0}

    machine_state["status"] = "COMPLETED"

    send_whatsapp("⏹️ Cycle Completed")

    print("Cycle completed")

    return jsonify({"status": "ack"})


# ================= ADMIN PANEL =================
@app.route("/admin")
def admin():
    return render_template("admin.html")


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
