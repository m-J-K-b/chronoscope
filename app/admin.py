from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


def setup_admin(app, db):
    from .calendar_feed_bp.models import CalendarFeed
    from .event_bp.models import Event

    admin = Admin(app, name="Admin Panel", template_mode="bootstrap3")
    admin.add_view(ModelView(CalendarFeed, db.session))
    admin.add_view(ModelView(Event, db.session))
