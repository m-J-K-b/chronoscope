from datetime import date, datetime
from typing import Optional

from dateutil import rrule

from app import db


# Model to store events from calendar feeds
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String, nullable=True)

    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=True)

    calendar_feed_id = db.Column(
        db.Integer, db.ForeignKey("calendar_feed.id"), nullable=False
    )

    def __init__(self) -> None:
        self._dates = None

    @property
    def start_date(self) -> date:
        return self.start_datetime.date()

    @property
    def start_date_str(self) -> date:
        return self.start_datetime.date().strftime("%d %M %Y")

    @property
    def end_date(self) -> date:
        return self.end_datetime.date()

    @property
    def dates(self):
        """Return the list of dates on which the event occurs."""
        if not hasattr(self, "_event_dates") or self._dates is None:
            # Calculate the list of dates for the event using dateutil.rrule
            self._dates = [
                dt.date()
                for dt in rrule.rrule(
                    rrule.DAILY, dtstart=self.start_date, until=self.end_date
                )
            ]

        return self._dates

    @property
    def start_time_str(self) -> str:
        return self.start_datetime.strftime("%H:%M")

    @property
    def countdown(self) -> str:
        return (self.start_date - date.today()).days

    @property
    def countdown_str(self) -> str:
        if self.countdown < -1:
            return f"{abs(self.countdown)} days ago"
        if self.countdown == -1:
            return f"yesterday"
        if self.countdown == 0:
            return f"today"
        if self.countdown == 1:
            return f"tomorrow"
        if self.countdown > 1:
            return f"in {self.countdown} days"
        return str(self.countdown)

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
