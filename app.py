from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "travel_secret_key"

bookings = []
vehicles = []

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
        else:
            error = "Wrong username or password"

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    total_bookings = len(bookings)
    total_vehicles = len(vehicles)
    pending_payments = len([b for b in bookings if b["payment_status"] == "Pending"])

    return render_template(
        "dashboard.html",
        bookings=bookings,
        total_bookings=total_bookings,
        total_vehicles=total_vehicles,
        pending_payments=pending_payments
    )


@app.route("/add-booking", methods=["GET", "POST"])
def add_booking():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        booking = {
            "customer_name": request.form["customer_name"],
            "mobile": request.form["mobile"],
            "pickup": request.form["pickup"],
            "drop": request.form["drop"],
            "date": request.form["date"],
            "time": request.form["time"],
            "vehicle": request.form["vehicle"],
            "amount": request.form["amount"],
            "payment_status": request.form["payment_status"]
        }

        bookings.append(booking)
        return redirect("/dashboard")

    return render_template("add_booking.html", vehicles=vehicles)


@app.route("/vehicles", methods=["GET", "POST"])
def vehicle_page():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        vehicle = {
            "vehicle_name": request.form["vehicle_name"],
            "vehicle_number": request.form["vehicle_number"],
            "driver_name": request.form["driver_name"],
            "driver_mobile": request.form["driver_mobile"],
            "status": request.form["status"]
        }

        vehicles.append(vehicle)
        return redirect("/vehicles")

    return render_template("vehicles.html", vehicles=vehicles)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
