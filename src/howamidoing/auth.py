import functools
import re

from bson.objectid import ObjectId
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from howamidoing.db import get_db
from howamidoing.objects import Profile

bp = Blueprint('auth', __name__, url_prefix='/auth')


def validate_username(username, users_collection):
    """
    Validate username. 

    - username: 4-50 chars. Alphanumeric characters, dots, 
      underscores, plus signs, hyphens, and "@" characters.
    """
    username_regex = re.compile(r"^[a-zA-Z0-9_.+@-]+$")
    reserved_words = ["admin", "administrator", "root", "user", "username", "test", "guest"]
    if len(username) < 4:
        return False, "Username must have at least 4 characters."

    if len(username) > 50:
        return False, "Username cannot exceed 50 characters."

    if not username_regex.match(username):
        return False, "Invalid characters."

    if username in reserved_words:
        return False, "Invalid username. Please try a different one."

    if users_collection.find_one({"username": username}):
        return False, f"User {username} is already registered"

    return True, None


def validate_password(password):
    """
    Validate username. Return error message or None if passed.

    - password: >8 chars. At least one lowercase, uppercase
      and number.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search("[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search("[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search("[0-9]", password):
        return False, "Password must contain at least one number."

    return True, None


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = get_db().users

        is_username_valid, username_error_message = validate_username(username, users)
        is_password_valid, password_error_message = validate_password(password)

        if not is_username_valid:
            flash(username_error_message, "error")
        if not is_password_valid:
            flash(password_error_message, "error")

        if is_username_valid and is_password_valid:
            # Create new profile for user and store user data
            profile = Profile()._to_json()
            password = generate_password_hash(password)
            users.insert_one({
                "username": username, 
                "password": password,
                "profile": profile
            })

            # Redirect to the login page
            return redirect(url_for("auth.login"))

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = get_db().users

        user = users.find_one({"username": username})

        if user and check_password_hash(user["password"], password):
            # store the user's _id in sessions
            session["user_id"] = str(user["_id"])
            return redirect(url_for("index"))
        else:
            flash("Incorrect username or password.")

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id =  ObjectId(session.get("user_id"))
    users = get_db().users

    if user_id is None:
        g.user = None
    else:
        g.user = users.find_one({"_id": user_id})
        if g.user:
            g.profile = Profile(g.user["profile"])


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view