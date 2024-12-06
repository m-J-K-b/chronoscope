from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db

from .forms import CalendarFeedCreationForm
from .models import CalendarFeed
from .utils import *

calendar_feed_bp = Blueprint(
    "calendar_feed_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@calendar_feed_bp.route("/add_calendar_feed", methods=["GET", "POST"])
def add_calendar_feed():
    form = CalendarFeedCreationForm()

    if form.validate_on_submit():  # Check if form passes validation
        if add_calendar_feed_from_url(form.name.data, form.url.data):
            flash("Calendar feed added successfully!", "success")
            return redirect(url_for("calendar_feed_bp.index"))

    if form.errors:
        flash("There was an error with your form. Please check your inputs.", "danger")

    # Render the template with the form
    return render_template("add_calendar_feed.html", form=form)


@calendar_feed_bp.route(
    "/delete_calendar_feed/<int:calendar_feed_id>", methods=["POST"]
)
def delete_calendar_feed(calendar_feed_id):
    CalendarFeed.query.get(calendar_feed_id).delete()
    db.session.commit()


@calendar_feed_bp.route("/manage_calendar_feed/<int:calendar_feed_id>", methods=["GET"])
def manage_calendar_feed(calendar_feed_id):
    calendar_feed = CalendarFeed.query.get(calendar_feed_id)
    if not calendar_feed:
        return "Calendar feed not found", 404  # Handle missing calendar feed
    return render_template("manage_calendar_feed.html", calendar_feed=calendar_feed)


@calendar_feed_bp.route("/", methods=["GET"])
def index():
    calendar_feeds = CalendarFeed.query.order_by(CalendarFeed.name).all()
    return render_template("manage_calendar_feeds.html", calendar_feeds=calendar_feeds)
