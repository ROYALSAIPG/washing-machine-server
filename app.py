@app.route("/test")
def test():
    send_whatsapp("🔥 Test working")
    return "sent"
