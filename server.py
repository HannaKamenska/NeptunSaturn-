from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Бот работает!"

@app.route("/ping")
def ping():
    return "pong", 200
