from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class EventCreationForm(FlaskForm):
    name = StringField("Event Name", validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[Optional()])
    description = StringField("Description", validators=[Optional()])
    calendar_feed_id = SelectField(
        "Calendar Feed", coerce=int, validators=[DataRequired()]
    )
    submit = SubmitField("Submit")
