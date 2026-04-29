from pathlib import Path
import zipfile

base = Path("/mnt/data/travel_owner_app_pro")
(base / "templates").mkdir(parents=True, exist_ok=True)
(base / "static").mkdir(exist_ok=True)

files = {}

files["app.py"] = r'''
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "travel-owner-pro-secret"

DB_PATH = Path("travel.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            mobile TEXT,
            pickup TEXT NOT NULL,
            drop_location TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            driver TEXT NOT NULL,
            vehicle TEXT,
            total_amount REAL NOT NULL,
            paid_amount REAL NOT NULL DEFAULT 0,
            pending_amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    conn = get_db()
    if search:
        bookings = conn.execute("""
            SELECT * FROM bookings
            WHERE customer_name LIKE ? OR mobile LIKE ? OR pickup LIKE ? OR drop_location LIKE ? OR driver LIKE ?
            ORDER BY id DESC
        """, tuple([f"%{search}%"] * 5)).fetchall()
    else:
        bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()

    totals = conn.execute("""
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total,
            COALESCE(SUM(paid_amount), 0) AS paid,
            COALESCE(SUM(pending_amount), 0) AS pending,
            COUNT(*) AS count
        FROM bookings
    """).fetchone()

    pending_count = conn.execute("SELECT COUNT(*) AS c FROM bookings WHERE status='Pending'").fetchone()["c"]
    paid_count = conn.execute("SELECT COUNT(*) AS c FROM bookings WHERE status='Paid'").fetchone()["c"]
    conn.close()

    return render_template(
        "index.html",
        bookings=bookings,
        totals=totals,
        pending_count=pending_count,
        paid_count=paid_count,
        search=search
    )

@app.route("/add", methods=["GET", "POST"])
def add_booking():
    if request.method == "POST":
        customer_name = request.form["customer_name"]
        mobile = request.form["mobile"]
        pickup = request.form["pickup"]
        drop_location = request.form["drop_location"]
        booking_date = request.form["booking_date"]
        booking_time = request.form["booking_time"]
        driver = request.form["driver"]
        vehicle = request.form["vehicle"]
        total_amount = float(request.form["total_amount"] or 0)
        paid_amount = float(request.form["paid_amount"] or 0)
        pending_amount = max(total_amount - paid_amount, 0)
        status = "Paid" if pending_amount == 0 else "Pending"

        conn = get_db()
        conn.execute("""
            INSERT INTO bookings
            (customer_name, mobile, pickup, drop_location, booking_date, booking_time,
             driver, vehicle, total_amount, paid_amount, pending_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, mobile, pickup, drop_location, booking_date, booking_time,
              driver, vehicle, total_amount, paid_amount, pending_amount, status))
        conn.commit()
        conn.close()

        flash("Booking successfully added!", "success")
        return redirect(url_for("index"))

    return render_template("booking_form.html", booking=None)

@app.route("/edit/<int:booking_id>", methods=["GET", "POST"])
def edit_booking(booking_id):
    conn = get_db()
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()

    if booking is None:
        conn.close()
        flash("Booking not found!", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        customer_name = request.form["customer_name"]
        mobile = request.form["mobile"]
        pickup = request.form["pickup"]
        drop_location = request.form["drop_location"]
        booking_date = request.form["booking_date"]
        booking_time = request.form["booking_time"]
        driver = request.form["driver"]
        vehicle = request.form["vehicle"]
        total_amount = float(request.form["total_amount"] or 0)
        paid_amount = float(request.form["paid_amount"] or 0)
        pending_amount = max(total_amount - paid_amount, 0)
        status = "Paid" if pending_amount == 0 else "Pending"

        conn.execute("""
            UPDATE bookings SET
            customer_name=?, mobile=?, pickup=?, drop_location=?, booking_date=?, booking_time=?,
            driver=?, vehicle=?, total_amount=?, paid_amount=?, pending_amount=?, status=?
            WHERE id=?
        """, (customer_name, mobile, pickup, drop_location, booking_date, booking_time,
              driver, vehicle, total_amount, paid_amount, pending_amount, status, booking_id))
        conn.commit()
        conn.close()

        flash("Booking updated successfully!", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("booking_form.html", booking=booking)

@app.route("/mark-paid/<int:booking_id>")
def mark_paid(booking_id):
    conn = get_db()
    conn.execute("""
        UPDATE bookings
        SET paid_amount = total_amount, pending_amount = 0, status = 'Paid'
        WHERE id = ?
    """, (booking_id,))
    conn.commit()
    conn.close()
    flash("Booking marked as paid!", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:booking_id>")
def delete_booking(booking_id):
    conn = get_db()
    conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    flash("Booking deleted!", "danger")
    return redirect(url_for("index"))

@app.route("/profile")
def profile():
    conn = get_db()
    bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    totals = conn.execute("""
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total,
            COALESCE(SUM(paid_amount), 0) AS paid,
            COALESCE(SUM(pending_amount), 0) AS pending,
            COUNT(*) AS count
        FROM bookings
    """).fetchone()
    conn.close()
    return render_template("profile.html", bookings=bookings, totals=totals)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
'''

files["templates/base.html"] = r'''
<!DOCTYPE html>
<html lang="mr">
<head>
    <meta charset="UTF-8">
    <title>Travel Owner Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='style.css') }}" rel="stylesheet">
</head>
<body>

<div class="sidebar">
    <div class="brand">
        <div class="brand-icon">🚕</div>
        <div>
            <h4>TravelPro</h4>
            <small>Owner Panel</small>
        </div>
    </div>

    <a href="{{ url_for('index') }}">🏠 Dashboard</a>
    <a href="{{ url_for('add_booking') }}">➕ Add Booking</a>
    <a href="{{ url_for('profile') }}">👤 My Profile</a>
</div>

<div class="main-content">
    <div class="topbar">
        <div>
            <h5 class="mb-0">Travel Booking Management</h5>
            <small>Pickup • Drop • Driver • Payment</small>
        </div>
        <a href="{{ url_for('add_booking') }}" class="btn btn-primary rounded-pill">+ New Booking</a>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, msg in messages %}
                <div class="alert alert-{{ category }} alert-dismissible fade show mt-3">
                    {{ msg }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>
'''

files["templates/index.html"] = r'''
{% extends "base.html" %}
{% block content %}

<section class="hero">
    <div>
        <p class="tag">Owner Dashboard</p>
        <h1>तुमच्या travel booking चे smart management</h1>
        <p class="hero-text">Booking add करा, payment track करा, pending amount पाहा आणि driver details manage करा.</p>
    </div>
    <div class="hero-card-mini">
        <span>Today Ready</span>
        <h2>₹{{ "%.0f"|format(totals.pending) }}</h2>
        <p>Pending Collection</p>
    </div>
</section>

<div class="row g-3 mt-2">
    <div class="col-lg-3 col-md-6">
        <div class="stat-card purple">
            <div class="stat-icon">📋</div>
            <span>Total Bookings</span>
            <h3>{{ totals.count }}</h3>
        </div>
    </div>
    <div class="col-lg-3 col-md-6">
        <div class="stat-card green">
            <div class="stat-icon">✅</div>
            <span>Paid Amount</span>
            <h3>₹{{ "%.2f"|format(totals.paid) }}</h3>
        </div>
    </div>
    <div class="col-lg-3 col-md-6">
        <div class="stat-card red">
            <div class="stat-icon">⏳</div>
            <span>Pending Amount</span>
            <h3>₹{{ "%.2f"|format(totals.pending) }}</h3>
        </div>
    </div>
    <div class="col-lg-3 col-md-6">
        <div class="stat-card blue">
            <div class="stat-icon">💰</div>
            <span>Total Business</span>
            <h3>₹{{ "%.2f"|format(totals.total) }}</h3>
        </div>
    </div>
</div>

<div class="content-card mt-4">
    <div class="card-head">
        <div>
            <h4>All Bookings</h4>
            <small>Paid: {{ paid_count }} | Pending: {{ pending_count }}</small>
        </div>

        <form method="GET" class="search-box">
            <input type="text" name="search" value="{{ search }}" placeholder="Search customer, driver, location..." class="form-control">
            <button class="btn btn-dark">Search</button>
            {% if search %}
                <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Clear</a>
            {% endif %}
        </form>
    </div>

    <div class="table-responsive">
        <table class="table booking-table align-middle">
            <thead>
                <tr>
                    <th>Customer</th>
                    <th>Route</th>
                    <th>Date & Time</th>
                    <th>Driver</th>
                    <th>Vehicle</th>
                    <th>Payment</th>
                    <th>Status</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
            {% for b in bookings %}
                <tr>
                    <td>
                        <b>{{ b.customer_name }}</b>
                        <div class="muted">{{ b.mobile }}</div>
                    </td>
                    <td>
                        <div class="route">
                            <span>📍 {{ b.pickup }}</span>
                            <span>➡️ {{ b.drop_location }}</span>
                        </div>
                    </td>
                    <td>
                        <b>{{ b.booking_date }}</b>
                        <div class="muted">{{ b.booking_time }}</div>
                    </td>
                    <td>{{ b.driver }}</td>
                    <td>{{ b.vehicle or "-" }}</td>
                    <td>
                        <div>Total: ₹{{ "%.2f"|format(b.total_amount) }}</div>
                        <div class="text-success">Paid: ₹{{ "%.2f"|format(b.paid_amount) }}</div>
                        <div class="text-danger">Pending: ₹{{ "%.2f"|format(b.pending_amount) }}</div>
                    </td>
                    <td>
                        {% if b.status == "Paid" %}
                            <span class="status paid">Paid</span>
                        {% else %}
                            <span class="status pending">Pending</span>
                        {% endif %}
                    </td>
                    <td class="text-end">
                        <a class="btn btn-sm btn-primary" href="{{ url_for('edit_booking', booking_id=b.id) }}">Edit</a>
                        {% if b.status != "Paid" %}
                            <a class="btn btn-sm btn-success" href="{{ url_for('mark_paid', booking_id=b.id) }}">Make Paid</a>
                        {% endif %}
                        <a class="btn btn-sm btn-outline-danger" onclick="return confirm('Booking delete करायची का?')" href="{{ url_for('delete_booking', booking_id=b.id) }}">Delete</a>
                    </td>
                </tr>
            {% else %}
                <tr>
                    <td colspan="8" class="empty-box">
                        <h5>No bookings found</h5>
                        <p>पहिली booking add करा.</p>
                        <a href="{{ url_for('add_booking') }}" class="btn btn-primary">Add Booking</a>
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>

{% endblock %}
'''

files["templates/booking_form.html"] = r'''
{% extends "base.html" %}
{% block content %}

<div class="form-wrapper">
    <div class="form-title">
        <p class="tag">{{ "Update Details" if booking else "New Entry" }}</p>
        <h2>{{ "Edit Booking" if booking else "Add New Booking" }}</h2>
        <p>Customer, route, driver आणि payment details भरा.</p>
    </div>

    <form method="POST" class="pro-form">
        <div class="section-title">Customer Details</div>
        <div class="row g-3">
            <div class="col-md-6">
                <label>Customer Name *</label>
                <input type="text" name="customer_name" class="form-control" required value="{{ booking.customer_name if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Mobile Number</label>
                <input type="text" name="mobile" class="form-control" value="{{ booking.mobile if booking else '' }}">
            </div>
        </div>

        <div class="section-title mt-4">Trip Details</div>
        <div class="row g-3">
            <div class="col-md-6">
                <label>Pickup Location *</label>
                <input type="text" name="pickup" class="form-control" required value="{{ booking.pickup if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Drop Location *</label>
                <input type="text" name="drop_location" class="form-control" required value="{{ booking.drop_location if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Date *</label>
                <input type="date" name="booking_date" class="form-control" required value="{{ booking.booking_date if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Time *</label>
                <input type="time" name="booking_time" class="form-control" required value="{{ booking.booking_time if booking else '' }}">
            </div>
        </div>

        <div class="section-title mt-4">Driver & Payment</div>
        <div class="row g-3">
            <div class="col-md-6">
                <label>Driver Name *</label>
                <input type="text" name="driver" class="form-control" required value="{{ booking.driver if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Vehicle</label>
                <input type="text" name="vehicle" class="form-control" placeholder="Swift Dzire / Ertiga / Innova" value="{{ booking.vehicle if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Total Payment *</label>
                <input type="number" step="0.01" name="total_amount" class="form-control" required value="{{ booking.total_amount if booking else '' }}">
            </div>
            <div class="col-md-6">
                <label>Paid Amount *</label>
                <input type="number" step="0.01" name="paid_amount" class="form-control" required value="{{ booking.paid_amount if booking else '0' }}">
            </div>
        </div>

        <div class="form-actions">
            <button class="btn btn-success btn-lg">💾 Save Booking</button>
            <a href="{{ url_for('index') }}" class="btn btn-light btn-lg">Back</a>
        </div>
    </form>
</div>

{% endblock %}
'''

files["templates/profile.html"] = r'''
{% extends "base.html" %}
{% block content %}

<section class="profile-hero">
    <div>
        <p class="tag">My Profile</p>
        <h1>Business Summary</h1>
        <p>तुमच्या सर्व booking, paid amount आणि pending amount चा report.</p>
    </div>
</section>

<div class="row g-3 mt-2">
    <div class="col-md-4">
        <div class="profile-card">
            <span>Total Paid</span>
            <h2 class="text-success">₹{{ "%.2f"|format(totals.paid) }}</h2>
        </div>
    </div>
    <div class="col-md-4">
        <div class="profile-card">
            <span>Total Pending</span>
            <h2 class="text-danger">₹{{ "%.2f"|format(totals.pending) }}</h2>
        </div>
    </div>
    <div class="col-md-4">
        <div class="profile-card">
            <span>Total Bookings</span>
            <h2>{{ totals.count }}</h2>
        </div>
    </div>
</div>

<div class="content-card mt-4">
    <div class="card-head">
        <h4>Booking History</h4>
    </div>

    <div class="row g-3">
        {% for b in bookings %}
            <div class="col-lg-6">
                <div class="history-card">
                    <div class="d-flex justify-content-between">
                        <h5>{{ b.customer_name }}</h5>
                        <span class="status {{ 'paid' if b.status == 'Paid' else 'pending' }}">{{ b.status }}</span>
                    </div>
                    <p class="mb-1">📍 {{ b.pickup }} → {{ b.drop_location }}</p>
                    <p class="mb-1">👨‍✈️ {{ b.driver }} | 🚗 {{ b.vehicle or "-" }}</p>
                    <p class="mb-1">🗓 {{ b.booking_date }} {{ b.booking_time }}</p>
                    <hr>
                    <div class="row">
                        <div class="col">Total<br><b>₹{{ "%.2f"|format(b.total_amount) }}</b></div>
                        <div class="col text-success">Paid<br><b>₹{{ "%.2f"|format(b.paid_amount) }}</b></div>
                        <div class="col text-danger">Pending<br><b>₹{{ "%.2f"|format(b.pending_amount) }}</b></div>
                    </div>
                </div>
            </div>
        {% else %}
            <div class="empty-box">
                <h5>No booking history</h5>
            </div>
        {% endfor %}
    </div>
</div>

{% endblock %}
'''

files["static/style.css"] = r'''
:root {
    --dark: #111827;
    --blue: #2563eb;
    --purple: #7c3aed;
    --green: #16a34a;
    --red: #dc2626;
    --bg: #f4f7fb;
    --text: #0f172a;
    --muted: #64748b;
}

* {
    box-sizing: border-box;
}

body {
    background: var(--bg);
    color: var(--text);
    font-family: Arial, sans-serif;
}

.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: 245px;
    height: 100vh;
    background: linear-gradient(180deg, #0f172a, #1e1b4b);
    padding: 24px 18px;
    color: white;
    z-index: 10;
}

.brand {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 34px;
}

.brand-icon {
    background: rgba(255,255,255,0.13);
    width: 52px;
    height: 52px;
    display: grid;
    place-items: center;
    border-radius: 18px;
    font-size: 26px;
}

.brand h4 {
    margin: 0;
    font-weight: 800;
}

.brand small {
    color: #cbd5e1;
}

.sidebar a {
    display: block;
    color: #e5e7eb;
    text-decoration: none;
    padding: 13px 14px;
    margin-bottom: 10px;
    border-radius: 14px;
    font-weight: 700;
    transition: 0.2s;
}

.sidebar a:hover {
    background: rgba(255,255,255,0.12);
    color: white;
}

.main-content {
    margin-left: 245px;
    padding: 24px;
}

.topbar {
    background: white;
    padding: 18px 22px;
    border-radius: 22px;
    box-shadow: 0 10px 30px rgba(15,23,42,0.07);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.topbar small, .muted {
    color: var(--muted);
}

.hero, .profile-hero {
    margin-top: 24px;
    background: radial-gradient(circle at top left, #3b82f6, #111827 55%);
    color: white;
    padding: 34px;
    border-radius: 30px;
    min-height: 210px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 20px 45px rgba(37,99,235,0.24);
}

.hero h1, .profile-hero h1 {
    max-width: 700px;
    font-weight: 900;
    line-height: 1.1;
}

.hero-text {
    max-width: 620px;
    color: #dbeafe;
    font-size: 17px;
}

.tag {
    display: inline-block;
    background: rgba(255,255,255,0.16);
    color: white;
    padding: 7px 14px;
    border-radius: 999px;
    font-weight: 700;
    margin-bottom: 10px;
}

.hero-card-mini {
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.22);
    backdrop-filter: blur(10px);
    padding: 24px;
    border-radius: 24px;
    min-width: 230px;
}

.hero-card-mini h2 {
    font-weight: 900;
    font-size: 42px;
}

.stat-card, .profile-card {
    background: white;
    padding: 22px;
    border-radius: 24px;
    box-shadow: 0 12px 30px rgba(15,23,42,0.07);
    min-height: 145px;
    border: 1px solid #eef2f7;
}

.stat-icon {
    width: 42px;
    height: 42px;
    border-radius: 15px;
    display: grid;
    place-items: center;
    background: #f1f5f9;
    font-size: 22px;
    margin-bottom: 12px;
}

.stat-card span, .profile-card span {
    color: var(--muted);
    font-weight: 700;
}

.stat-card h3, .profile-card h2 {
    margin-top: 8px;
    font-weight: 900;
}

.stat-card.green { border-bottom: 5px solid var(--green); }
.stat-card.red { border-bottom: 5px solid var(--red); }
.stat-card.blue { border-bottom: 5px solid var(--blue); }
.stat-card.purple { border-bottom: 5px solid var(--purple); }

.content-card {
    background: white;
    border-radius: 26px;
    box-shadow: 0 12px 30px rgba(15,23,42,0.07);
    overflow: hidden;
    padding: 22px;
}

.card-head {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
    margin-bottom: 18px;
}

.card-head h4 {
    margin: 0;
    font-weight: 900;
}

.search-box {
    display: flex;
    gap: 8px;
    min-width: 420px;
}

.booking-table thead th {
    color: #475569;
    background: #f8fafc;
    border-bottom: none;
    font-size: 13px;
    text-transform: uppercase;
}

.booking-table td {
    padding: 16px 10px;
}

.route {
    display: grid;
    gap: 4px;
}

.status {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 13px;
}

.status.paid {
    background: #dcfce7;
    color: #166534;
}

.status.pending {
    background: #fee2e2;
    color: #991b1b;
}

.form-wrapper {
    max-width: 980px;
    margin: 24px auto;
}

.form-title {
    background: linear-gradient(120deg, #2563eb, #111827);
    color: white;
    padding: 30px;
    border-radius: 28px 28px 0 0;
}

.form-title h2 {
    font-weight: 900;
}

.pro-form {
    background: white;
    padding: 30px;
    border-radius: 0 0 28px 28px;
    box-shadow: 0 12px 30px rgba(15,23,42,0.08);
}

.section-title {
    font-weight: 900;
    color: #1e293b;
    border-left: 5px solid var(--blue);
    padding-left: 10px;
}

label {
    font-weight: 800;
    margin-bottom: 7px;
}

.form-control {
    border-radius: 14px;
    padding: 12px 14px;
    border: 1px solid #dbe3ef;
}

.form-control:focus {
    box-shadow: 0 0 0 4px rgba(37,99,235,0.12);
    border-color: var(--blue);
}

.form-actions {
    margin-top: 28px;
    display: flex;
    gap: 10px;
}

.history-card {
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 20px;
    background: #fbfdff;
    height: 100%;
}

.history-card h5 {
    font-weight: 900;
}

.empty-box {
    text-align: center;
    padding: 50px !important;
    color: var(--muted);
}

@media (max-width: 900px) {
    .sidebar {
        position: relative;
        width: 100%;
        height: auto;
    }

    .main-content {
        margin-left: 0;
        padding: 14px;
    }

    .hero {
        display: block;
    }

    .hero-card-mini {
        margin-top: 20px;
    }

    .topbar, .card-head {
        display: block;
    }

    .search-box {
        min-width: 100%;
        margin-top: 14px;
        flex-wrap: wrap;
    }
}
'''

files["requirements.txt"] = "Flask==3.0.3\n"

files["Dockerfile"] = r'''
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
'''

files[".gitignore"] = r'''
__pycache__/
*.pyc
travel.db
.env
venv/
'''
# Travel Owner Pro App

#Python Flask + SQLite app for travel booking owners.

## Features

- Add booking
- Edit full booking
- Delete booking
- Make Pending payment as Paid
- Search bookings
- Pickup and Drop details
- Date and Time
- Driver and Vehicle
- Total, Paid, Pending amount
- My Profile business summary
- Data saved in SQLite database

## Run

```bash
pip install -r requirements.txt
