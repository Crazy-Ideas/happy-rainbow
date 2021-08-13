from functools import wraps
from typing import List

from flask import render_template, request, url_for, Response, make_response, redirect, current_app, flash, send_file
from flask_login import login_user, current_user, logout_user
from werkzeug.urls import url_parse

from app import app, get_user_from_token
from certificate import create_certificate, certificate_download, certificate_delete, batch_certificate_delete
from config import Config, today
from forms import LoginForm, WorkshopForm, WorkshopDeleteForm, ParticipantForm, ParticipantDeleteForm
from models import Workshop, Participant


def cookie_login_required(route_function):
    @wraps(route_function)
    def decorated_route(*args, **kwargs):
        if current_user.is_authenticated:
            return route_function(*args, **kwargs)
        token: str = request.cookies.get("token")
        user = get_user_from_token(token)
        if user:
            login_user(user=user)
            return route_function(*args, **kwargs)
        return current_app.login_manager.unauthorized()

    return decorated_route


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/workshops/future", methods=["GET", "POST"])
@cookie_login_required
def upcoming_workshops():
    workshops: List[Workshop] = Workshop.objects.filter("date", ">=", today()).get()
    workshops.sort(key=lambda workshop: workshop.date)
    form = WorkshopDeleteForm()
    if not form.validate_on_submit():
        return render_template("upcoming_workshop.html", title="Upcoming Workshops", workshops=workshops, form=form)
    form.workshop.delete()
    return redirect(url_for("upcoming_workshops"))


@app.route("/workshops/past", methods=["GET", "POST"])
@cookie_login_required
def completed_workshops():
    workshops: List[Workshop] = Workshop.objects.filter("date", "<=", today()).get()
    workshops.sort(key=lambda workshop: workshop.date, reverse=True)
    form = WorkshopDeleteForm()
    if not form.validate_on_submit():
        return render_template("completed_workshop.html", title="Completed Workshops", workshops=workshops, form=form)
    batch_certificate_delete(form.workshop_id.data)
    return redirect(url_for("completed_workshops"))


@app.route("/workshops/<workshop_id>/certificate_url")
@cookie_login_required
def certificate_url(workshop_id: str):
    workshop: Workshop = Workshop.get_by_id(workshop_id)
    if not workshop:
        flash("Invalid workshop id.")
        return redirect(url_for("completed_workshops"))
    workshop.generate_url()
    return render_template("certificate_url.html", title="Certificate Link", workshop=workshop)


@app.route("/workshops/<workshop_id>/certificate/<signature>", methods=["GET", "POST"])
def certificate_preparation(workshop_id: str, signature: str):
    workshop: Workshop = Workshop.get_by_id(workshop_id)
    if not workshop or not workshop.valid_signature(signature):
        return render_template("participant_form.html", workshop=None)
    form = ParticipantForm()
    if not form.validate_on_submit():
        return render_template("participant_form.html", workshop=workshop, form=form, participant=Participant())
    participant: Participant = Participant.objects.filter_by(workshop_id=workshop_id,
                                                             name_key=form.participant.name_key).first()
    if participant:
        if not participant.certificate_pdf:
            participant.certificate_pdf = create_certificate(workshop, participant)
        participant.name = form.participant.name
        participant.phone = form.participant.phone
        participant.save()
    else:
        participant = form.participant
        participant.certificate_pdf = create_certificate(workshop, participant)
        participant.workshop_id = workshop_id
        participant.create()
        workshop.participants += 1
        workshop.save()
    return render_template("participant_form.html", workshop=workshop, form=form, participant=participant,
                           signature=signature)


@app.route("/workshops/<workshop_id>/participants", methods=["GET", "POST"])
@cookie_login_required
def view_participants(workshop_id: str):
    workshop: Workshop = Workshop.get_by_id(workshop_id)
    if not workshop or workshop.participants == 0:
        flash("All attendees deleted.")
        return redirect(url_for("completed_workshops"))
    participants: List[Participant] = Participant.objects.filter_by(workshop_id=workshop_id).get()
    form = ParticipantDeleteForm()
    if not form.validate_on_submit():
        return render_template("participants.html", workshop=workshop, participants=participants, form=form,
                               title="Workshop Attendees")
    certificate_delete(form.participant.certificate_pdf)
    form.participant.delete()
    workshop.participants -= 1
    workshop.save()
    return redirect(url_for("view_participants", workshop_id=workshop_id))


@app.route("/workshops/create", methods=["GET", "POST"])
@cookie_login_required
def create_workshop():
    form = WorkshopForm()
    if not form.validate_on_submit():
        return render_template("workshop_form.html", form=form, title="Add Workshop", create=True)
    form.workshop.create()
    return redirect(url_for("upcoming_workshops"))


@app.route("/workshops/update/<workshop_id>", methods=["GET", "POST"])
@cookie_login_required
def update_workshop(workshop_id: str):
    workshop: Workshop = Workshop.get_by_id(workshop_id)
    if not workshop:
        flash("Error in retrieving workshop details.")
        return redirect(url_for("home"))
    form = WorkshopForm(workshop)
    if not form.validate_on_submit():
        return render_template("workshop_form.html", form=form, title="Edit Workshop", create=False)
    form.workshop.save()
    return redirect(url_for("upcoming_workshops"))


@app.route("/workshops/<workshop_id>/participants/<participant_id>/download/<signature>")
def download(workshop_id: str, participant_id: str, signature: str):
    workshop: Workshop = Workshop.get_by_id(workshop_id)
    participant: Participant = Participant.get_by_id(participant_id)
    if not workshop or not participant or (not workshop.valid_signature(signature) and current_user.is_anonymous):
        return render_template("participant_form.html", workshop=None)
    file_path = certificate_download(participant.certificate_pdf)
    filename = f"Happy Rainbow Certificate - {participant.name}.pdf"
    return send_file(file_path, as_attachment=True, attachment_filename=filename)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("login.html", form=form)
    token = form.user.get_token()
    login_user(user=form.user)
    next_page = request.args.get("next")
    if not next_page or url_parse(next_page).netloc != str():
        next_page = url_for("upcoming_workshops")
    response: Response = make_response(redirect(next_page))
    response.set_cookie("token", token, max_age=Config.TOKEN_EXPIRY, secure=Config.CI_SECURITY, httponly=True,
                        samesite="Strict")
    return response


@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.revoke_token()
        logout_user()
    return redirect(url_for("home"))
