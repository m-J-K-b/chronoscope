from datetime import datetime
from typing import Optional

from dateutil import rrule

from app import db


# Model to store events from calendar feeds
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String, nullable=True)

    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)

    calendar_feed_id = db.Column(
        db.Integer, db.ForeignKey("calendar_feed.id"), nullable=False
    )

    # def __init__(self, start_datetime: datetime, end_datetime: datetime):
    #     self.start_datetime = start_datetime
    #     self.end_datetime = end_datetime
    #     self._event_dates = None  # To cache the event dates

    # @property
    # def event_dates(self):
    #     """Return the list of dates on which the event occurs."""
    #     if not hasattr(self, "_event_dates") or self._event_dates is None:
    #         # Calculate the list of dates for the event using dateutil.rrule
    #         start_date = self.start_datetime.date()
    #         end_date = self.end_datetime.date() if self.end_datetime else start_date

    #         # Generate the dates from start_date to end_date
    #         self._event_dates = list(
    #             rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)
    #         )

    #     return self._event_dates

    # @property
    # def duration_days(self) -> Optional[int]:
    #     """Calculate the total duration of the event in days."""
    #     if self.start_datetime and self.end_datetime:
    #         return (
    #             self.end_datetime - self.start_datetime
    #         ).days + 1  # Inclusive of start and end dates
    #     return None

    # def active_duration_string(self, from_datetime: Optional[datetime] = None) -> str:
    #     """
    #     Generate a string representing the current active day of the event
    #     and its total duration in days.
    #     """
    #     from_datetime = from_datetime or datetime.now()

    #     # Ensure start_datetime is defined
    #     if not self.start_datetime:
    #         return ""

    #     # Calculate total duration
    #     total_days = self.duration_days
    #     if total_days is None or total_days <= 0:
    #         return ""

    #     # Calculate active day
    #     days_since_start = (from_datetime.date() - self.start_datetime.date()).days + 1
    #     if days_since_start < 1:  # Event hasn't started yet
    #         return ""
    #     if days_since_start > total_days:  # Event has already ended
    #         return ""

    #     return f"Day {days_since_start} / {total_days}"

    # def days_until_start(
    #     self, from_datetime: Optional[datetime] = None
    # ) -> Optional[int]:
    #     """Calculate days until the event starts."""
    #     from_datetime = from_datetime or datetime.now()
    #     if self.start_datetime:
    #         return (self.start_datetime.date() - from_datetime.date()).days
    #     return None

    # def days_until_end(self, from_datetime: Optional[datetime] = None) -> Optional[int]:
    #     """Calculate days until the event ends."""
    #     from_datetime = from_datetime or datetime.now()
    #     if self.end_datetime:
    #         return (self.end_datetime.date() - from_datetime.date()).days
    #     return None

    # def count_down_string(self, from_datetime: Optional[datetime] = None) -> str:
    #     """Generate a countdown string for the event."""
    #     from_datetime = from_datetime or datetime.now()
    #     days_until_start = self.days_until_start(from_datetime)
    #     days_until_end = self.days_until_end(from_datetime)

    #     if days_until_start is not None and days_until_start > 0:
    #         return (
    #             f"Starts in {days_until_start} day{'s' if days_until_start > 1 else ''}"
    #         )
    #     elif days_until_start == 0:
    #         return "Starts today"
    #     elif days_until_end is not None:
    #         if days_until_end > 0:
    #             return (
    #                 f"Ends in {days_until_end} day{'s' if days_until_end > 1 else ''}"
    #             )
    #         elif days_until_end == 0:
    #             return "Ends today"

    #     return "This event has already ended"
