import datetime
from datetime import date

from flask import Blueprint, render_template

from .event_bp.models import Event

main = Blueprint("main", __name__, template_folder="templates")


@main.route("/", methods=["GET"])
def index():
    events = Event.query.all()
    events_sorted_by_date = {}
    for event in events:
        for d in event.dates:
            date_group = events_sorted_by_date.setdefault(d, [])
            date_group.append(event)
    sorted_dates = sorted(events_sorted_by_date.keys())
    current_date = date.today()
    current_date_index = next(
        (i for i, date in enumerate(sorted_dates) if date >= current_date), None
    )

    return render_template(
        "index.html",
        upcoming_event_info_str="Over the next two weeks, a major tech company will launch a highly anticipated smartwatch, showcasing advanced health-tracking features that are expected to make waves in the wearable tech market. On Tuesday, a severe snowstorm is forecasted to disrupt travel in the northeastern United States, leading to widespread delays at airports and affecting holiday plans for thousands of travelers. By Wednesday, a viral video of a heroic animal rescue operation will capture the public's heart, sparking renewed conversations about wildlife preservation. Thursday will bring a major medical breakthrough with the publication of a groundbreaking study on the treatment of chronic illnesses, drawing significant attention from both the medical community and the public. On Friday, a star player in a popular sports league will be traded, igniting debates about the team's future prospects. Over the weekend, a major music festival will take place, drawing thousands of fans and providing a platform for emerging artists, while social media is flooded with live updates and exclusive content. Finally, an art exhibition opening on Sunday will feature contemporary works and offer interactive workshops for art enthusiasts.",
        sorted_dates=sorted_dates,
        current_date_index=current_date_index,
        events_sorted_by_date=events_sorted_by_date,
    )
