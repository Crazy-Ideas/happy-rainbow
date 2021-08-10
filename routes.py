from functools import wraps
from typing import List

from flask import render_template, request, url_for, Response, make_response, redirect, current_app
from flask_login import login_user, current_user, logout_user
from werkzeug.urls import url_parse

from app import app, get_user_from_token
from config import Config, today
from forms import LoginForm, WorkshopForm
from models import Workshop


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


@app.route("/workshops/future")
@cookie_login_required
def upcoming_workshops():
    workshops: List[Workshop] = Workshop.objects.filter("date", ">=", today()).get()
    workshops.sort(key=lambda workshop: workshop.date)
    return render_template("workshop_list.html", title="Upcoming Workshops", workshops=workshops)


@app.route("/workshops/create", methods=["GET", "POST"])
@cookie_login_required
def create_workshop():
    form = WorkshopForm()
    if not form.validate_on_submit():
        return render_template("workshop_create.html", form=form, title="Add Workshop")
    form.workshop.create()
    return redirect(url_for("upcoming_workshops"))


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
