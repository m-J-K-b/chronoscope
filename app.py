import os
import secrets
from datetime import date, datetime, timezone
from operator import methodcaller

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from icalendar import Calendar

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# Configure the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///calendars.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


migrate = Migrate(app, db)


# Model to store calendar feed URLs
class CalendarFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Custom name for the feed
    url = db.Column(db.String(500), unique=True, nullable=True)
    events = db.relationship("Event", backref="feed", cascade="all, delete", lazy=True)
    owned = db.Column(db.Boolean, default=False)


# Model to store events from calendar feeds
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String, nullable=True)

    start_datetime = db.Column(db.DateTime, nullable=False)  # Start date as string
    end_datetime = db.Column(db.DateTime, nullable=True)  # End date as string

    calendar_feed_id = db.Column(
        db.Integer, db.ForeignKey("calendar_feed.id"), nullable=False
    )


# Create the database tables
with app.app_context():
    db.create_all()


# Function to fetch and parse ICS feed from URL
def fetch_ics_feed(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {url}\n{e}")
        return None


# Function to calculate days until the event, considering timezone awareness
def days_until_event(event_date):
    today = datetime.now()

    # Check if event_date is timezone-aware
    if (
        event_date.tzinfo is not None
        and event_date.tzinfo.utcoffset(event_date) is not None
    ):
        # Convert the current date to timezone-aware in UTC
        today = today.astimezone(timezone.utc)

    # Calculate the difference
    delta = event_date - today
    return delta.days


# Function to process each calendar feed and store events in the database
def process_calendar_feed(feed):
    ics_data = fetch_ics_feed(feed.url)
    if not ics_data:
        return False

    # Parse the ICS data
    try:
        calendar = Calendar.from_ical(ics_data)
    except Exception as e:
        print(f"Error parsing calendar feed from {feed.url}\n{e}")
        return False

    # Clear any existing events for this feed to avoid duplicates
    Event.query.filter_by(calendar_feed_id=feed.id).delete()
    db.session.commit()

    # Loop through the events and calculate days until each event
    for component in calendar.walk():
        if component.name == "VEVENT":
            name = component.get("summary")
            start_datetime = component.get("dtstart").dt
            end_datetime = component.get("dtend").dt
            description = component.get("description")

            if end_datetime == None:
                end_datetime = start_datetime

            # Handle all-day events (which are `date` objects)
            if isinstance(start_datetime, date):
                start_datetime = datetime.combine(start_datetime, datetime.min.time())
            if isinstance(end_datetime, date):
                end_datetime = datetime.combine(end_datetime, datetime.min.time())

            # Store the start and end dates
            new_event = Event(
                name=name,
                description=description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                calendar_feed_id=feed.id,
            )

            db.session.add(new_event)

    db.session.commit()
    return True


@app.route("/reprocess_feeds")
def reprocess_feeds():
    # Fetch IDs of all imported calendar feeds
    imported_feed_ids = (
        CalendarFeed.query.filter_by(owned=False).with_entities(CalendarFeed.id).all()
    )

    # Flatten the list of tuples to a list of IDs
    imported_feed_ids = [feed_id[0] for feed_id in imported_feed_ids]

    # Clear existing events to avoid duplication
    Event.query.filter(Event.calendar_feed_id.in_(imported_feed_ids)).delete()

    # Fetch the feeds for reprocessing
    imported_feeds = CalendarFeed.query.filter_by(owned=False).all()

    # Process each feed and handle any errors
    for feed in imported_feeds:
        if not process_calendar_feed(feed):
            flash(f"Feed '{feed.name}' couldn't be processed", "danger")

    flash("All feeds have been reprocessed.", "success")
    return redirect(url_for("manage_feeds"))


@app.route("/apply_filter", methods=["POST"])
def apply_filter():
    # Get the selected feed IDs from the form
    selected_feed_ids = request.form.getlist("feed")

    # Store the selected feed IDs in the session
    session["selected_feed_ids"] = selected_feed_ids

    # Flash message to notify that the filter has been applied
    flash("Filter has been applied.", "success")

    # Redirect to the index page
    return redirect("/")


@app.route("/clear_filter")
def clear_filter():
    session.pop("selected_feed_ids", None)  # Remove selected_feed_ids from session
    flash("Filter has been cleared.", "info")
    return redirect("/")


@app.route("/add_feed", methods=["POST"])
def add_feed():
    if request.method == "POST":
        feed_url = request.form["url"]
        feed_name = request.form["name"]  # Get the custom name for the feed

        # Check if the feed already exists
        if not CalendarFeed.query.filter_by(url=feed_url).first():
            # Add the new feed with the custom name
            new_feed = CalendarFeed(url=feed_url, name=feed_name)
            db.session.add(new_feed)
            db.session.commit()
            if process_calendar_feed(new_feed):
                flash("Feed has been added.", "success")
            else:
                flash("Feed couldn't be processed.", "danger")
        else:
            flash("Feed with this URL already exists.", "danger")

        return redirect(url_for("manage_feeds"))


@app.route("/create_calendar", methods=["POST"])
def create_calendar():
    if request.method == "POST":
        feed_name = request.form["name"]  # Get the custom name for the owned calendar

        # Create a new owned calendar
        if not CalendarFeed.query.filter_by(name=feed_name).first():
            new_calendar = CalendarFeed(
                name=feed_name, url=None, owned=True
            )  # Set url to None for owned calendars
            db.session.add(new_calendar)
            db.session.commit()
            flash("Calendar has been created.", "success")
        else:
            flash("Calendar with this name already exists.", "danger")

    return redirect(url_for("manage_feeds"))


@app.route("/delete_feed/<int:feed_id>", methods=["POST"])
def delete_feed(feed_id):
    feed = CalendarFeed.query.get_or_404(feed_id)

    # Delete the feed and its associated events
    db.session.delete(feed)
    db.session.commit()

    flash("Feed has been removed.", "success")

    return redirect(url_for("manage_feeds"))


@app.route("/add_event", methods=["POST"])
def add_event():
    if request.method == "POST":
        name = request.form["name"]
        start_datetime_str = request.form["start_datetime"]
        end_datetime_str = request.form["end_datetime"]
        description = request.form["description"]
        calendar_id = int(request.form["calendar_id"])

        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%dT%H:%M")

        # Here you would add the logic to save the event to the database.
        new_event = Event(
            calendar_feed_id=calendar_id,
            name=name,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        db.session.add(new_event)
        db.session.commit()

        flash("Event added successfully!", "success")
    return redirect("/")  # Redirect back to the events page


# Route to display all events from the database
@app.route("/", methods=["GET", "POST"])
def index():
    selected_feed_ids = session.get("selected_feed_ids", [])
    today = datetime.now()

    owned_feeds = CalendarFeed.query.filter_by(owned=True).all()

    # If no feeds are selected, show all events
    events = Event.query.filter(Event.end_datetime > today).order_by(
        Event.start_datetime
    )
    if selected_feed_ids:
        # Filter events based on selected feeds
        events = events.filter(Event.calendar_feed_id.in_(selected_feed_ids))
    events = events.all()
    for event in events:
        event.days_until_start = (event.start_datetime - today).days
        event.days_until_end = (event.end_datetime - today).days

    return render_template(
        "index.html",
        events=events,
        feeds=CalendarFeed.query.all(),
        owned_feeds=owned_feeds,
        selected_feeds=selected_feed_ids,
    )


@app.route("/manage_feeds")
def manage_feeds():
    # Fetch all the existing calendar feeds to display them
    owned_feeds = CalendarFeed.query.filter_by(owned=True).all()
    imported_feeds = CalendarFeed.query.filter_by(owned=False).all()
    return render_template(
        "manage_feeds.html", imported_feeds=imported_feeds, owned_feeds=owned_feeds
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
