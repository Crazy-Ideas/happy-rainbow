from datetime import datetime
from typing import Optional, List

import pytz
from flask import request
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField, HiddenField
from wtforms.validators import InputRequired, ValidationError

from models import User, Workshop


class WorkshopForm(FlaskForm):
    INVALID_DATE_TEXT: str = "Invalid Date."
    title: StringField = StringField("Title", validators=[InputRequired()], description="E.g. Fevicryl Workshop")
    topic: StringField = StringField("Topic", validators=[InputRequired()],
                                     description="The topic to be covered in the workshop.")
    date: StringField = StringField("Date", validators=[InputRequired()],
                                    description="Enter date in dd/mm/yy format. For e.g. 26/9/21")
    time: StringField = StringField("Time", validators=[InputRequired()],
                                    description="Enter start time and end time of workshop. For e.g. 2:00 to 3:30 pm")
    instructor: StringField = StringField("Instructor", validators=[InputRequired()], default="Darshini")
    venue: StringField = StringField("Venue", validators=[InputRequired()], default="Zoom")
    submit: SubmitField = SubmitField("Add Workshop")

    def __init__(self, workshop: Workshop = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workshop: Workshop = workshop if workshop else Workshop()
        if request.method == "GET" and workshop:
            self.title.data = workshop.title
            self.topic.data = workshop.topic
            self.date.data = workshop.date.strftime("%d/%m/%y")
            self.time.data = workshop.time
            self.instructor.data = workshop.instructor
            self.venue.data = workshop.venue

    def validate_title(self, title: StringField):
        self.workshop.title = title.data

    def validate_topic(self, topic: StringField):
        self.workshop.topic = topic.data

    def validate_date(self, date: StringField):
        dmy_str_list: List[str] = date.data.split("/")
        try:
            day: int = int(dmy_str_list[0])
            month: int = int(dmy_str_list[1])
            year: int = int(dmy_str_list[2])
            dmy_datetime: datetime = datetime(day=day, month=month, year=2000 + year, tzinfo=pytz.UTC)
        except (ValueError, IndexError):
            raise ValidationError(self.INVALID_DATE_TEXT)
        self.workshop.date = dmy_datetime

    def validate_time(self, time: StringField):
        self.workshop.time = time.data

    def validate_instructor(self, instructor: StringField):
        self.workshop.instructor = instructor.data

    def validate_venue(self, venue: StringField):
        self.workshop.venue = venue.data


class WorkshopDeleteForm(FlaskForm):
    ERROR_TEXT: str = "Invalid workshop id."
    workshop_id: HiddenField = HiddenField()
    submit: SubmitField = SubmitField("Yes - Delete")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workshop: Optional[Workshop] = None

    def validate_workshop_id(self, workshop_id: HiddenField):
        if not workshop_id.data:
            raise ValidationError(self.ERROR_TEXT)
        self.workshop: Workshop = Workshop.get_by_id(workshop_id.data)
        if not self.workshop:
            raise ValidationError(self.ERROR_TEXT)


class LoginForm(FlaskForm):
    ERROR_TEXT: str = "Invalid email or password."
    email: StringField = StringField("Email", validators=[InputRequired()],
                                     description="Please contact info@crazyideas.co.in for login credentials.")
    password: PasswordField = PasswordField("Password", validators=[InputRequired()],
                                            description="You can save your password in the browser.")
    submit: SubmitField = SubmitField("Sign In")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: Optional[User] = None

    def validate_password(self, password: PasswordField):
        self.user: User = User.objects.filter_by(email=self.email.data).first()
        if not self.user:
            raise ValidationError(self.ERROR_TEXT)
        if not self.user.check_password(password.data):
            raise ValidationError(self.ERROR_TEXT)
        return
