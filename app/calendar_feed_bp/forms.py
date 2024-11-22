from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Optional


class CalendarFeedCreationForm(FlaskForm):
    name = StringField("Event Name", validators=[DataRequired()])
    url = StringField("URL", validators=[Optional()])
    submit = SubmitField("Submit")
