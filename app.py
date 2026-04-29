from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///travel.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------ MODEL ------------------
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pickup = db.Column(db.String(100))
    drop_location = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    vehicle = db.Column(db.String(50))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    driver = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    status = db.Column(db.String(20), default="Pending")


# ------------------ LOGIN ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin":
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Login Failed"

    return """
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    """


# ------------------ DASHBOARD ------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    bookings = Booking.query.all()

    total_paid = sum(b.amount for b in bookings if b.status == "Paid")
    total_pending = sum(b.amount for b in bookings if b.status == "Pending")

    return render_template("dashboard.html",
                           bookings=bookings,
                           paid=total_paid,
                           pending=total_pending)


# ------------------ ADD BOOKING ------------------
@app.route("/add", methods=["GET", "POST"])
def add_booking():
    if request.method == "POST":
        new = Booking(
            pickup=request.form["pickup"],
            drop_location=request.form["drop_location"],
            contact=request.form["contact"],
            vehicle=request.form["vehicle"],
            date=request.form["date"],
            time=request.form["time"],
            driver=request.form["driver"],
            amount=request.form["amount"],
            status=request.form["status"]
        )
        db.session.add(new)
        db.session.commit()
        return redirect("/dashboard")

    return render_template("add_booking.html")


# ------------------ EDIT ------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_booking(id):
    booking = Booking.query.get_or_404(id)

    if request.method == "POST":

        # Confirm झाल्यावर फक्त amount edit
        if booking.status == "Confirmed":
            booking.amount = request.form["amount"]

        else:
            booking.pickup = request.form["pickup"]
            booking.drop_location = request.form["drop_location"]
            booking.contact = request.form["contact"]
            booking.vehicle = request.form["vehicle"]
            booking.date = request.form["date"]
            booking.time = request.form["time"]
            booking.driver = request.form["driver"]
            booking.amount = request.form["amount"]
            booking.status = request.form["status"]

        db.session.commit()
        return redirect("/dashboard")

    return render_template("edit_booking.html", booking=booking)


# ------------------ CONFIRM ------------------
@app.route("/confirm/<int:id>")
def confirm_booking(id):
    booking = Booking.query.get_or_404(id)
    booking.status = "Confirmed"
    db.session.commit()
    return redirect("/dashboard")


# ------------------ DELETE ------------------
@app.route("/delete/<int:id>")
def delete_booking(id):
    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    return redirect("/dashboard")


# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ------------------ RUN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
