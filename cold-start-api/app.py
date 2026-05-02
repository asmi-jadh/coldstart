from flask import Flask, render_template, request
import joblib
import sqlite3

from azure import predict_azure


from gcp_09 import generate_features


# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect("prediction.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS RESULT(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_type TEXT,
        latency REAL,
        request_count REAL,
        avg REAL,
        spread REAL,
        ratio REAL,
        memory REAL,
        mem_spread REAL,
        prediction TEXT,
        probability REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()   # ✅ FIXED
    conn.close()    # ✅ FIXED

init_db()

# ---------------- APP ----------------
app = Flask(__name__)

# Load models
model = joblib.load("model/new_model.pkl")   # GCP
azure_model = joblib.load("model/model_afternoon.pkl")

#azure_model = joblib.load("model/morning_random_forest_model.joblib")

# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    prediction = None
    probability = None

    if request.method == "POST":

        model_type = request.form["model_type"]

        # -------- GCP --------
        if model_type == "gcp":
            latency = float(request.form["latency"])
            request_count = float(request.form["request"])
            hour = int(request.form["hour"])
            day = int(request.form["day"])

            X = [generate_features(hour, day, request_count, latency)]
            prob = model.predict_proba(X)[0][1]

            if latency > 500 or request_count > 200:
                prob = max(prob, 0.9)
            elif latency < 200 and request_count < 50:
                prob = min(prob, 0.3)

        # -------- AZURE --------
        elif model_type == "azure":
            avg = float(request.form["avg"])
            spread = float(request.form["spread"])
            ratio = float(request.form["ratio"])
            memory = float(request.form["memory"])
            mem_spread = float(request.form["mem_spread"])

            prob = predict_azure(
                azure_model,
                avg, spread, ratio, memory, mem_spread
            )

        # -------- OUTPUT --------
        if prob < 0.3:
            prediction = "No Cold Start"
        elif prob < 0.7:
            prediction = "Medium Cold Start Risk"
        else:
            prediction = "Cold Start Likely"

        probability = round(prob, 2)

        # -------- STORE IN DB --------
        conn = sqlite3.connect("prediction.db")
        c = conn.cursor()

        if model_type == "gcp":
            c.execute("""
            INSERT INTO RESULT
            (model_type, latency, request_count, prediction, probability)
            VALUES (?, ?, ?, ?, ?)
            """, ("gcp", latency, request_count, prediction, probability))

        elif model_type == "azure":
            c.execute("""
            INSERT INTO RESULT
            (model_type, avg, spread, ratio, memory, mem_spread, prediction, probability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("azure", avg, spread, ratio, memory, mem_spread, prediction, probability))

        conn.commit()   # ✅ moved OUTSIDE
        conn.close()    # ✅ moved OUTSIDE

    return render_template("index.html",
                           prediction=prediction,
                           probability=probability)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)