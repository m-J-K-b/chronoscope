import logging
from datetime import date, datetime
from typing import Optional

import requests
from flask import flash
from icalendar import Calendar

from app import db
from app.calendar_feed_bp.models import CalendarFeed
from app.event_bp.models import Event

logging.basicConfig(level=logging.INFO)


def fetch_ics_from_url(url: str) -> Optional[str]:
    """Fetch the ICS file from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch URL: {url}. Error: {e}")
        return None


def process_calendar_feed(calendar_feed: CalendarFeed) -> bool:
    """Sync the events from the given calendar feed."""
    ics_data = fetch_ics_from_url(calendar_feed.url)
    if not ics_data:
        return False

    # Parse the ICS data
    try:
        calendar = Calendar.from_ical(ics_data)
    except Exception as e:
        logging.error(
            f"Error parsing calendar feed from {calendar_feed.url}. Error: {e}"
        )
        return False

    # Ensure calendar_feed.id is assigned
    db.session.add(calendar_feed)
    db.session.flush()

    # Clear any existing events for this feed
    Event.query.filter_by(calendar_feed_id=calendar_feed.id).delete()

    # Process events from ICS
    for component in calendar.walk():
        if component.name == "VEVENT":
            try:
                name = component.get("summary", "Untitled Event")
                description = component.get("description", "No description provided")
                start_datetime = component.get("dtstart")
                end_datetime = component.get("dtend")

                if not start_datetime:
                    logging.warning("Skipping event with no start date.")
                    continue

                start_datetime = start_datetime.dt
                end_datetime = end_datetime.dt if end_datetime else None

                # Ensure all times are datetime objects
                if isinstance(start_datetime, date) and not isinstance(
                    start_datetime, datetime
                ):
                    start_datetime = datetime.combine(
                        start_datetime, datetime.min.time()
                    )
                if (
                    end_datetime
                    and isinstance(end_datetime, date)
                    and not isinstance(end_datetime, datetime)
                ):
                    end_datetime = datetime.combine(end_datetime, datetime.min.time())

                # Check for duplicate events
                existing_event = Event.query.filter_by(
                    name=name,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    calendar_feed_id=calendar_feed.id,
                ).first()

                if not existing_event:
                    new_event = Event(
                        name=name,
                        description=description,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        calendar_feed_id=calendar_feed.id,
                    )
                    db.session.add(new_event)
            except Exception as e:
                logging.error(
                    f"Error processing component {component}. Feed: {calendar_feed.url}. Error: {e}"
                )

    db.session.commit()
    return True


def add_calendar_feed_from_url(name: str, url: str) -> bool:
    """Add a calendar feed to the database and fetch its events."""
    calendar_feed = CalendarFeed(name=name, url=url)
    if CalendarFeed.query.filter_by(url=url).count():
        flash("Warning, Calendar with this url exists!", "warning")
    if process_calendar_feed(calendar_feed):
        db.session.add(calendar_feed)
        db.session.commit()
        return True
    return False
