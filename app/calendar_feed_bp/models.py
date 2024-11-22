from app import db


class CalendarFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Custom name for the feed
    url = db.Column(db.String(500), unique=True, nullable=True)
    events = db.relationship("Event", backref="feed", cascade="all, delete", lazy=True)
    owned = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<CalendarFeed {self.name}>"
