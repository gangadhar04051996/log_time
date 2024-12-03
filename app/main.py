from datetime import time, timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import uuid
from database import init_db, db_session
from models import User, LogEntry
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)

# Initialize the database
init_db()

# Helper function to calculate the nearest time interval
def generate_time_intervals():
    intervals = []
    start_time = datetime.strptime("06:00 AM", "%I:%M %p")
    end_time = datetime.strptime("06:00 PM", "%I:%M %p")
    while start_time < end_time:
        interval_start = start_time.strftime("%I:%M %p")
        interval_end = (start_time + timedelta(minutes=30)).strftime("%I:%M %p")
        intervals.append(f"{interval_start} to {interval_end}")
        start_time += timedelta(minutes=30)
    return intervals


def get_nearest_interval(timeslots):
    now = datetime.now()
    for slot in timeslots:
        start, end = slot.split(" to ")
        start_time = datetime.strptime(start, "%I:%M %p").time()
        end_time = datetime.strptime(end, "%I:%M %p").time()
        if start_time <= now.time() < end_time:
            return slot
    return timeslots[-1]


def get_secret_key():
    # Check if the SECRET_KEY environment variable is set
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        return secret_key

    # If the environment variable is not set, use the file-based approach
    if not os.path.exists(SECRET_FILE):
        # Generate a new secret key and save it
        with open(SECRET_FILE, "w") as f:
            secret = os.urandom(24).hex()  # 48-character hex key
            f.write(secret)
            return secret
    else:
        # Load the existing secret key
        with open(SECRET_FILE, "r") as f:
            return f.read().strip()


SECRET_FILE = "secret_key.txt"
app.secret_key = get_secret_key()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        username = request.form["username"]

        # Check if username already exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            flash("Username already taken. Please choose a different one.", "error")
            return redirect(url_for("register"))

        # Generate unique ID and store user in the database
        unique_id = str(uuid.uuid4())  # Generate a unique ID
        new_user = User(first_name=first_name, last_name=last_name, username=username, unique_id=unique_id)
        db_session.add(new_user)
        db_session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("login_register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        last_name = request.form["last_name"]

        # Authenticate user
        user = db_session.query(User).filter_by(username=username, last_name=last_name).first()
        if user:
            session["user_id"] = user.id  # Store user ID in the session
            session["username"] = user.username
            flash(f"Welcome back, {user.first_name}!", "success")
            return redirect(url_for("index"))

        flash("Invalid username or last name. Please try again.", "error")
        return redirect(url_for("login"))

    return render_template("login_register.html")


@app.route("/logout")
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        flash("Please log in to access your logs.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    username = session.get("username", "Unknown User")
    timeslots = generate_time_intervals()  # Use the corrected function
    default_interval = get_nearest_interval(timeslots)


    if request.method == "POST":
        time_interval = request.form["time_interval"]
        description = request.form["description"]
        if not description.strip():
            flash("Description cannot be empty.", "error")
            return redirect(url_for("index"))
            return render_template(
                "index.html",
                timeslots=timeslots,
                default_interval=default_interval,
                error="Description cannot be empty.",
            )
        log = LogEntry(
            user_id=user_id,  # Use the user ID from the session
            timestamp=datetime.now(),
            interval=time_interval,
            description=description,
        )
        db_session.add(log)
        db_session.commit()

        flash("Log entry added successfully!", "success")
        return redirect(url_for("index"))
        return render_template(
            "index.html",
            timeslots=timeslots,
            default_interval=default_interval,
            success="Log entry added successfully!",
        )
    return render_template("index.html", timeslots=timeslots, default_interval=default_interval, username=username)

import random
from datetime import datetime
from pytz import timezone, utc
@app.route("/logs", methods=["GET"])
def view_logs():

    local_tz = timezone("America/New_York")

    if "user_id" not in session:
        flash("Please log in to view your logs.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    username = session.get("username", "Unknown User")

    # Get selected date or default to today
    selected_date = request.args.get("log_date", datetime.now().strftime("%Y-%m-%d"))
    selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
    today = datetime.now().date()

    # Check if the selected date is in the future
    if selected_datetime.date() > today:
        future_messages = [
            "Time traveling is still experimental. No logs! 🚀",
            "We checked... still no logs in the future! 🕒",
            "No logs from the future yet, but keep dreaming big! 💭",
            "You seem to have outrun the calendar. Slow down! 🏃‍♂️",
            "Future logs? Not even Marty McFly left those! 🛹",
        ]
        random_message = random.choice(future_messages)
        return render_template(
            "view_logs.html",
            logs=[],
            selected_date=selected_date,
            random_message=random_message,
            time_travel = True,
            username=username,
        )
    logs = (
        db_session.query(LogEntry)
        .filter(LogEntry.user_id == user_id)
        .filter(LogEntry.timestamp >= f"{selected_date} 00:00:00")
        .filter(LogEntry.timestamp <= f"{selected_date} 23:59:59")
        .order_by(LogEntry.timestamp.desc())
        .all()
    )

    for log in logs:
    # Convert timestamp string to datetime
        if isinstance(log.timestamp, str):
            log.timestamp = datetime.strptime(log.timestamp[:-7], "%Y-%m-%d %H:%M:%S")  # Adjust format as needed
        # Perform timezone conversion
        log.timestamp = utc.localize(log.timestamp).astimezone(local_tz)

    funny_messages = [
        "Oops, no adventures logged today! 📜",
        "The logs are taking a day off. 🛌",
        "It’s awfully quiet here... no logs found. 🤔",
        "Nothing to see here, folks! 🚷",
        "Oh no! The log elves are on vacation. 🎄",
        "Ohhh..., we have no logs! 🚀",
        "Nothing here. Did you forget to log, or Did you sleep all day? 😴"
        "The logs are hiding... try another date! 🕵️‍♂️",
    ]

    random_message = random.choice(funny_messages)

    return render_template(
        "view_logs.html",
        logs=logs,
        selected_date=selected_date,
        random_message=random_message,
        username=username
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
