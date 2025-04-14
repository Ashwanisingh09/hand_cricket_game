# -----------------------------
# app.py
# -----------------------------
from flask import Flask, render_template, request, session, redirect, url_for
import random
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session or "player2" not in session:
        return redirect(url_for("set_username_page"))

    if "user_score" not in session:
        session["user_score"] = 0
        session["player2_score"] = 0
        session["game_over"] = False
        session["out"] = False

    message = ""
    result = ""

    if request.method == "POST" and not session["game_over"]:
        user_input = int(request.form["choice"])

        if session["batting"] == "player1":
            comp_input = random.randint(1, 6) if session.get("vs_computer") else int(request.form["player2_choice"])

            if user_input == comp_input:
                message = f"{session['username']} is OUT! Now {session['player2']}'s turn."
                session["batting"] = "player2"
                session["out"] = False
            else:
                session["user_score"] += user_input
                message = f"{session['username']} chose {user_input}, {session['player2']} chose {comp_input}."

        elif session["batting"] == "player2":
            if session.get("vs_computer"):
                comp_choice = random.randint(1, 6)
                user_random = random.randint(1, 6)
                if comp_choice == user_random:
                    message = f"Computer is OUT!"
                    session["game_over"] = True
                else:
                    session["player2_score"] += comp_choice
                    message = f"Computer scored {comp_choice}!"

                if session["player2_score"] > session["user_score"]:
                    session["game_over"] = True
            else:
                comp_input = int(request.form["player2_choice"])
                if user_input == comp_input:
                    message = f"{session['player2']} is OUT!"
                    session["game_over"] = True
                else:
                    session["player2_score"] += comp_input
                    message = f"{session['player2']} chose {comp_input}, {session['username']} bowled {user_input}."

                if session["player2_score"] > session["user_score"]:
                    session["game_over"] = True

    if session["game_over"]:
        p1 = session["username"]
        p2 = session["player2"]
        if session["user_score"] > session["player2_score"]:
            result = f"🏆 {p1} Wins!"
            res_type = "Win"
        elif session["user_score"] < session["player2_score"]:
            result = f"🏆 {p2} Wins!"
            res_type = "Lose"
        else:
            result = "🤝 It's a Tie!"
            res_type = "Tie"

        log_history(p1, session["user_score"], session["player2_score"], res_type)

    return render_template("index.html",
                           message=message,
                           result=result,
                           user_score=session["user_score"],
                           computer_score=session["player2_score"],
                           game_over=session["game_over"],
                           batting=session.get("batting"),
                           username=session["username"],
                           player2=session["player2"],
                           vs_computer=session["vs_computer"])

@app.route("/set_username", methods=["GET", "POST"])
def set_username_page():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["player2"] = request.form["player2"].strip() or "Computer"
        session["vs_computer"] = not bool(request.form["player2"].strip())
        return redirect(url_for("toss_page"))
    return render_template("username.html")

@app.route("/toss", methods=["GET", "POST"])
def toss_page():
    if request.method == "POST":
        user_call = request.form["call"]
        actual = random.choice(["Heads", "Tails"])
        session["toss_result"] = actual
        session["toss_winner"] = session["username"] if user_call == actual else session["player2"]
        return redirect(url_for("toss_decision"))
    return render_template("toss.html", username=session["username"])

@app.route("/toss-decision", methods=["GET", "POST"])
def toss_decision():
    if request.method == "POST":
        choice = request.form["decision"]
        if session["toss_winner"] == session["username"]:
            session["batting"] = "player1" if choice == "Bat" else "player2"
        else:
            session["batting"] = "player2" if choice == "Bat" else "player1"
        session["user_score"] = 0
        session["player2_score"] = 0
        session["game_over"] = False
        session["out"] = False
        return redirect(url_for("index"))

    return render_template("toss_decision.html",
                           winner=session["toss_winner"],
                           is_user=session["toss_winner"] == session["username"])

@app.route("/leaderboard")
def leaderboard():
    try:
        with open("history.json", "r") as f:
            entries = [json.loads(line) for line in f.readlines()]
    except FileNotFoundError:
        entries = []

    leaderboard = {}
    for entry in entries:
        user = entry["username"]
        if user not in leaderboard:
            leaderboard[user] = {"Win": 0, "Lose": 0, "Tie": 0}
        leaderboard[user][entry["result"]] += 1

    return render_template("leaderboard.html", leaderboard=leaderboard)

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for('index'))

def log_history(username, user_score, player2_score, result):
    log_entry = {
        "username": username,
        "user_score": user_score,
        "computer_score": player2_score,
        "result": result,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("history.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

if __name__ == "__main__":
    app.run(debug=True)