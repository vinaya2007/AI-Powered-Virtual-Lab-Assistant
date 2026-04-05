from flask import Flask, render_template, request, jsonify
from chatbot import chatbot

app = Flask(__name__)


# 🏠 Welcome Page
@app.route("/")
def home():
    return render_template("index.html")


# 📂 Department Selection Page
@app.route("/department")
def department():
    return render_template("department.html")

@app.route("/viva")
def viva():
    return render_template("viva.html")

@app.route("/experiments")
def experiments():
    return render_template("experiments.html")

# 🎓 Year Selection Page
@app.route("/year")
def year():
    dept = request.args.get("dept")  # get department from URL
    return render_template("year.html", dept=dept)


# 📊 Dashboard Page
@app.route("/dashboard")
def dashboard():
    dept = request.args.get("dept")
    year = request.args.get("year")
    return render_template("dashboard.html", dept=dept, year=year)


# 💬 Chatbot Page
@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")


# 💬 Chat API (VERY IMPORTANT)
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")

    # safety check
    if not user_input:
        return jsonify({
            "text": "Please enter a message.",
            "image": None,
            "graph": None,
            "pdf": None
        })

    response = chatbot(user_input)

    # ensure all keys exist (important for frontend)
    response.setdefault("text", "")
    response.setdefault("image", None)
    response.setdefault("graph", None)
    response.setdefault("pdf", None)

    return jsonify(response)


# ▶ Run Server (ALWAYS LAST)
# if __name__ == "__main__":
    # app.run(debug=True)
if __name__ == "__main__":
    app.run()
