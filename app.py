from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "travel_owner_secret"

USERNAME = "admin"
PASSWORD = "1234"

def db():
    conn = sqlite3.connect("travel.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            contact_number TEXT,
            pickup TEXT,
            drop_location TEXT,
            date TEXT,
            time TEXT,
            vehicle_number TEXT,
            driver_name TEXT,
            total_payment REAL,
            paid_amount REAL,
            payment_status TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            vehicle_number TEXT,
            amount REAL,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["user"] = USERNAME
            return redirect("/dashboard")
        return render_template("login.html", error="Wrong username or password")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = db()
    bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    maintenance = conn.execute("SELECT * FROM maintenance ORDER BY id DESC").fetchall()

    total_payment = sum([b["total_payment"] or 0 for b in bookings])
    paid_amount = sum([b["paid_amount"] or 0 for b in bookings])
    pending_amount = total_payment - paid_amount
    maintenance_amount = sum([m["amount"] or 0 for m in maintenance])
    final_profit = paid_amount - maintenance_amount

    conn.close()

    return render_template(
        "dashboard.html",
        bookings=bookings,
        maintenance=maintenance,
        total_payment=total_payment,
        paid_amount=paid_amount,
        pending_amount=pending_amount,
        maintenance_amount=maintenance_amount,
        final_profit=final_profit
    )

@app.route("/add", methods=["GET", "POST"])
def add_booking():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        conn = db()
        total = float(request.form.get("total_payment") or request.form.get("amount") or 0)
        paid = float(request.form.get("paid_amount") or request.form.get("paid") or 0)
        status = "Paid" if paid >= total else "Pending"

        conn.execute("""
            INSERT INTO bookings
            (customer_name, contact_number, pickup, drop_location, date, time,
             vehicle_number, driver_name, total_payment, paid_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["customer_name"],
            request.form["contact_number"],
            request.form["pickup"],
            request.form["drop_location"],
            request.form["date"],
            request.form["time"],
            request.form["vehicle_number"],
            request.form["driver_name"],
            total,
            paid,
            status
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("add_booking.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_booking(id):
    if "user" not in session:
        return redirect("/")

    conn = db()
    booking = conn.execute("SELECT * FROM bookings WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        customer_name = request.form["customer_name"]
        contact_number = request.form["contact_number"]
        pickup = request.form["pickup"]
        drop_location = request.form["drop_location"]
        date = request.form["date"]
        time = request.form["time"]
        vehicle_number = request.form["vehicle_number"]
        driver_name = request.form["driver_name"]

        total = float(request.form["total_payment"])
        paid = float(request.form["paid_amount"])

        # ❌ validation
        if paid > total:
            conn.close()
            return render_template("edit_booking.html",
                                   booking=booking,
                                   error="Paid amount cannot be greater than Total ❌")

        # ✔️ status auto
        status = "Paid" if paid >= total else "Pending"

        conn.execute("""
            UPDATE bookings SET
            customer_name=?, contact_number=?, pickup=?, drop_location=?,
            date=?, time=?, vehicle_number=?, driver_name=?,
            total_payment=?, paid_amount=?, payment_status=?
            total = float(request.form["total_payment"])
            WHERE id=?
        """, (
            customer_name,
            contact_number,
            pickup,
            drop_location,
            date,
            time,
            vehicle_number,
            driver_name,
            total,
            paid,
            status,
            id
        ))

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    conn.close()
    return render_template("edit_booking.html", booking=booking)
@app.route("/delete/<int:id>")
def delete_booking(id):
    if "user" not in session:
        return redirect("/")

    conn = db()
    conn.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/maintenance", methods=["GET", "POST"])
def maintenance():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        conn = db()
        conn.execute("""
            INSERT INTO maintenance (title, vehicle_number, amount, date)
            VALUES (?, ?, ?, ?)
        """, (
            request.form["title"],
            request.form["vehicle_number"],
            float(request.form["amount"]),
            request.form["date"]
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("maintenance.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
