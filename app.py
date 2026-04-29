from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "travel_owner_secret"

DATABASE = "travel.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
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
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count > 0:
        conn.close()
        return redirect("/login")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    conn.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        conn.close()
        return redirect("/register")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Wrong username or password")

    conn.close()
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cursor.fetchall()

    cursor.execute("SELECT SUM(total_payment), SUM(paid_amount) FROM bookings")
    result = cursor.fetchone()

    total_payment = result[0] if result[0] else 0
    paid_amount = result[1] if result[1] else 0
    pending_amount = total_payment - paid_amount

    conn.close()

    return render_template(
        "dashboard.html",
        bookings=bookings,
        total_payment=total_payment,
        paid_amount=paid_amount,
        pending_amount=pending_amount
    )


@app.route("/add_booking", methods=["GET", "POST"])
def add_booking():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        customer_name = request.form.get("customer_name")
        contact_number = request.form.get("contact_number")
        pickup = request.form.get("pickup")
        drop_location = request.form.get("drop_location")
        date = request.form.get("date")
        time = request.form.get("time")
        vehicle_number = request.form.get("vehicle_number")
        driver_name = request.form.get("driver_name")

        total_payment = float(request.form.get("total_payment") or 0)
        paid_amount = float(request.form.get("paid_amount") or 0)

        status = "Paid" if paid_amount >= total_payment else "Pending"

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bookings (
                customer_name, contact_number, pickup, drop_location,
                date, time, vehicle_number, driver_name,
                total_payment, paid_amount, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name, contact_number, pickup, drop_location,
            date, time, vehicle_number, driver_name,
            total_payment, paid_amount, status
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_booking.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_booking(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (id,))
    booking = cursor.fetchone()

    if booking is None:
        conn.close()
        return redirect("/dashboard")

    if booking[11] == "Confirmed":
        conn.close()
        return redirect("/dashboard")

    if request.method == "POST":
        customer_name = request.form.get("customer_name")
        contact_number = request.form.get("contact_number")
        pickup = request.form.get("pickup")
        drop_location = request.form.get("drop_location")
        date = request.form.get("date")
        time = request.form.get("time")
        vehicle_number = request.form.get("vehicle_number")
        driver_name = request.form.get("driver_name")

        total_payment = float(request.form.get("total_payment") or 0)
        paid_amount = float(request.form.get("paid_amount") or 0)

        status = "Paid" if paid_amount >= total_payment else "Pending"

        cursor.execute("""
            UPDATE bookings SET
                customer_name = ?,
                contact_number = ?,
                pickup = ?,
                drop_location = ?,
                date = ?,
                time = ?,
                vehicle_number = ?,
                driver_name = ?,
                total_payment = ?,
                paid_amount = ?,
                status = ?
            WHERE id = ?
        """, (
            customer_name, contact_number, pickup, drop_location,
            date, time, vehicle_number, driver_name,
            total_payment, paid_amount, status, id
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    conn.close()
    return render_template("edit_booking.html", booking=booking)


@app.route("/confirm/<int:id>")
def confirm_booking(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET status = ? WHERE id = ?",
        ("Confirmed", id)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
