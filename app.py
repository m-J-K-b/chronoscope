import requests
from icalendar import Calendar
from datetime import datetime, timezone, date
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model to store calendar feed URLs
class CalendarFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Custom name for the feed
    url = db.Column(db.String(500), unique=True, nullable=False)
    events = db.relationship('Event', backref='feed', cascade="all, delete", lazy=True)


# Model to store events from calendar feeds
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.String(100), nullable=False)
    days_until = db.Column(db.Integer, nullable=False)
    calendar_feed_id = db.Column(db.Integer, db.ForeignKey('calendar_feed.id'), nullable=False)

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
    if event_date.tzinfo is not None and event_date.tzinfo.utcoffset(event_date) is not None:
        # Convert the current date to timezone-aware in UTC
        today = today.astimezone(timezone.utc)
    
    # Calculate the difference
    delta = event_date - today
    return delta.days

# Function to process each calendar feed and store events in the database
def process_calendar_feed(feed):
    ics_data = fetch_ics_feed(feed.url)
    if not ics_data:
        return
    
    # Parse the ICS data
    try:
        calendar = Calendar.from_ical(ics_data)
    except Exception as e:
        print(f"Error parsing calendar feed from {feed.url}\n{e}")
        return
    
    # Clear any existing events for this feed to avoid duplicates
    Event.query.filter_by(calendar_feed_id=feed.id).delete()
    db.session.commit()
    
    # Loop through the events and calculate days until each event
    for component in calendar.walk():
        if component.name == "VEVENT":
            event_name = component.get('summary')
            event_start = component.get('dtstart').dt

            # Handle all-day events (which are `date` objects)
            if isinstance(event_start, date) and not isinstance(event_start, datetime):
                # Convert `date` to a `datetime` at midnight (00:00)
                event_start = datetime.combine(event_start, datetime.min.time())
                
            if isinstance(event_start, datetime):
                # Skip past events
                if event_start < datetime.now(event_start.tzinfo):
                    continue
            
            # Calculate days until the event
            days_until = days_until_event(event_start)
            
            # Add the event to the database
            new_event = Event(
                name=event_name,
                start_date=event_start.strftime('%Y-%m-%d %H:%M'),
                days_until=days_until,
                calendar_feed_id=feed.id
            )
            db.session.add(new_event)
    
    db.session.commit()

# Route to display all events from the database
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        # Get the selected feed IDs from the form
        selected_feed_ids = request.form.getlist('feed')

        # If no feeds are selected, show all events
        if not selected_feed_ids:
            events = Event.query.order_by(Event.days_until).all()
        else:
            # Filter events based on selected feeds
            events = Event.query.filter(Event.calendar_feed_id.in_(selected_feed_ids)).order_by(Event.days_until).all()
    else:
        # Show all events by default if no filter is applied
        events = Event.query.order_by(Event.days_until).all()

    # Fetch all calendar feeds for the filtering form
    feeds = CalendarFeed.query.all()
    
    return render_template('events.html', events=events, feeds=feeds)

@app.route("/new_feed")
def new_feed():
    # Fetch all the existing calendar feeds to display them
    feeds = CalendarFeed.query.all()
    return render_template('new_feed.html', feeds=feeds)

@app.route("/add_feed", methods=['POST'])
def add_feed():
    if request.method == 'POST':
        feed_url = request.form['url']
        feed_name = request.form['name']  # Get the custom name for the feed
        
        # Check if the feed already exists
        if not CalendarFeed.query.filter_by(url=feed_url).first():
            # Add the new feed with the custom name
            new_feed = CalendarFeed(url=feed_url, name=feed_name)
            db.session.add(new_feed)
            db.session.commit()
            process_calendar_feed(new_feed)
        return redirect(url_for('new_feed'))

@app.route("/delete_feed/<int:feed_id>", methods=['POST'])
def delete_feed(feed_id):
    feed = CalendarFeed.query.get_or_404(feed_id)
    
    # Delete the feed and its associated events
    db.session.delete(feed)
    db.session.commit()
    
    return redirect(url_for('new_feed'))

if __name__ == "__main__":
    app.run(debug=True)
