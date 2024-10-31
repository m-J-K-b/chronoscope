import os
import secrets
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urljoin, urlparse

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

    @property
    def duration(self):
        """Calculate the duration of the event."""
        if self.end_datetime:
            return self.end_datetime - self.start_datetime
        else:
            return None

    @property
    def days_until_start(self):
        """Calculate days until the event starts."""
        if self.start_datetime:
            return (self.start_datetime.date() - datetime.now().date()).days
        return None

    @property
    def days_until_end(self):
        """Calculate days until the event ends."""
        if self.end_datetime:
            return (self.end_datetime.date() - datetime.now().date()).days
        return None


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

            if (end_datetime.date() - start_datetime.date()).days == 1:
                end_datetime = start_datetime

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
    redirect_url = request.args.get("redirect_url", "")

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

    # Sanitize and validate the redirect_url
    redirect_url = urljoin(request.host_url, redirect_url)  # Combine with base URL
    parsed_url = urlparse(redirect_url)

    if parsed_url.scheme in ("http", "https") and parsed_url.netloc == request.host:
        return redirect(redirect_url)

    return redirect(url_for("index"))


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


@app.route("/add_calendar", methods=["POST"])
def add_calendar():
    feed_name = request.form["name"]
    feed_url = request.form.get("url")

    # Check for existing calendar or feed
    existing = CalendarFeed.query.filter(
        (CalendarFeed.url == feed_url) | (CalendarFeed.name == feed_name)
    ).first()

    if existing:
        flash(
            (
                "Feed with this URL already exists."
                if feed_url
                else "Calendar with this name already exists."
            ),
            "danger",
        )
    else:
        new_feed = CalendarFeed(name=feed_name, url=feed_url, owned=feed_url is None)
        db.session.add(new_feed)
        db.session.commit()

        if feed_url and not process_calendar_feed(new_feed):
            flash("Feed couldn't be processed.", "danger")
        else:
            flash(
                (
                    "Calendar has been created."
                    if feed_url is None
                    else "Feed has been added."
                ),
                "success",
            )

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
    today_date = date.today()
    today_datetime = datetime.combine(today_date, time.min)

    owned_feeds = CalendarFeed.query.filter_by(owned=True).all()

    events = Event.query.filter(Event.end_datetime >= today_datetime).order_by(
        Event.start_datetime
    )
    if selected_feed_ids:
        events = events.filter(Event.calendar_feed_id.in_(selected_feed_ids))
    events = events.all()

    # Prepare data structure to group events by date
    events_by_date = {}
    for event in events:
        # Get the start date for the event
        start_date = event.start_datetime.date()
        end_date = event.end_datetime.date()

        # Add events to the dictionary for all days from start to end
        current_date = start_date
        while current_date >= today_date and current_date <= end_date:
            if current_date not in events_by_date:
                events_by_date[current_date] = []
            events_by_date[current_date].append(event)
            current_date += timedelta(days=1)

    # Sort the dates
    sorted_dates = sorted(events_by_date.keys())

    # Get upcoming events
    upcoming_events = [event for event in events if 0 < event.days_until_start < 5]

    # Sort upcoming events by days_until_start
    upcoming_events_sorted = sorted(upcoming_events, key=lambda e: e.days_until_start)

    # Pass data to the template
    num_upcoming_events = len(upcoming_events)
    first_upcoming_event = upcoming_events_sorted[0] if upcoming_events_sorted else None

    return render_template(
        "index.html",
        events_by_date=events_by_date,
        sorted_dates=sorted_dates,
        feeds=CalendarFeed.query.all(),
        owned_feeds=owned_feeds,
        selected_feeds=selected_feed_ids,
        num_upcoming_events=num_upcoming_events,
        first_upcoming_event=first_upcoming_event,
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
