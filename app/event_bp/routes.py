from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.calendar_feed_bp.models import CalendarFeed

from .forms import EventCreationForm
from .models import Event

event_bp = Blueprint(
    "event_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@event_bp.route("/add_event", methods=["GET", "POST"])
def add_event():
    form = EventCreationForm()

    form.calendar_feed_id.choices = [
        (calendar.id, calendar.name) for calendar in CalendarFeed.query.all()
    ]

    if form.validate_on_submit():  # Check if form passes validation
        # Create a new Event instance with form data
        new_event = Event(
            calendar_feed_id=form.calendar_feed_id.data,
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
        )

        # Add the new event to the database
        db.session.add(new_event)
        db.session.commit()

        flash("Event added successfully!", "success")
        return redirect(url_for("event_bp.index"))  # Redirect to a relevant page

    if form.errors:
        flash("There was an error with your form. Please check your inputs.", "danger")

    # Render the template with the form
    return render_template("add_event.html", form=form)


@event_bp.route("/manage_event/<int:event_id>", methods=["GET"])
def manage_event(event_id):
    event = Event().query.get(event_id)
    if not event:
        return "Calendar feed not found", 404  # Handle missing calendar feed
    return render_template("manage_event.html", event=event)


@event_bp.route("/")
def index():
    events = Event.query.order_by(Event.name).all()
    return render_template("manage_events.html", events=events)
