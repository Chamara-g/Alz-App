import functools

from datetime import datetime
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif (
            db.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone()
            is not None
        ):
            error = "User {0} is already registered.".format(username)

        if error is None:
            # the name is available, store it in the database and go to
            # the login page

            create_user_db(db, username, password, '', '')

            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))

@bp.route("/glogin/", methods=["POST"])
def glogin():
    email = request.form["email"]
    given_name = request.form["given_name"]
    profile_id = request.form["profile_id"]
    image_url = request.form["image_url"]

    db = get_db()
    user = db.execute(
        "SELECT * FROM user WHERE username = ?", (email,)
    ).fetchone()

    if user is None:
        # Register User
        create_user_db(db, email, profile_id, given_name, image_url)
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (email,)
        ).fetchone()

    else:
        # Update user last login
        update_last_login(db, user["id"])

    session.clear()
    session["user_id"] = user["id"]

    return redirect(url_for("index"))


def create_user_db(db, username, password, given_name, image_url ):
    db.execute(
        "INSERT INTO user (username, password, given_name, image_url, last_login) VALUES (?, ?, ?, ?, ?)",
        (username, generate_password_hash(password), given_name, image_url, datetime.now()),
    )
    db.commit()

    # Adding user to results
    user_id = UserResult.get_user_id(username)
    db.execute(
        "INSERT INTO results (user_id, filename) VALUES (?, ?)",
        (user_id, ''),
    )
    db.commit()

    # Adding user to modeling
    db.execute(
        "INSERT INTO modeling (user_id, trained_file) VALUES (?, ?)",
        (user_id, ''),
    )
    db.commit()

    return True

def update_last_login(db, user_id):
    db.execute(
        "UPDATE user SET last_login = ? WHERE id = ?",
        (datetime.now(), user_id),
    )
    db.commit()


class UserResult:

    def get_user_id(username):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()
        if user is not None:
            return user["id"]
        return None

    def get_user_results(user_id):
        db = get_db()
        result = db.execute(
            "SELECT * FROM results WHERE user_id = ?", (user_id,)
        ).fetchone()
        if result is not None:
            return result
        return None

    def update_result(user_id, column, value):
        db = get_db()
        db.execute(
            "UPDATE results SET " + column +" = ? WHERE user_id = ?",( value, user_id),
        )
        db.commit()

    def update_selected_col(selected_col, user_id):
        db = get_db()
        db.execute(
            "UPDATE results SET  col_method1 = ?, col_method2 = ?, col_method3 = ? WHERE user_id = ?", (selected_col[0],selected_col[1], selected_col[2], user_id),
        )
        db.commit()

    def update_modeling(user_id, column, value):
        db = get_db()
        db.execute(
            "UPDATE modeling SET " + column +" = ? WHERE user_id = ?",( value, user_id),
        )
        db.commit()

    def get_user_model(user_id):
        db = get_db()
        result = db.execute(
            "SELECT * FROM modeling WHERE user_id = ?", (user_id,)
        ).fetchone()
        if result is not None:
            return result
        return None