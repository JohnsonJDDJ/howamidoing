# A Blueprint is a way to organize a group of related views 
# and other code. Rather than registering views and other 
# code directly with an application, they are registered 
# with a blueprint

# The authentication blueprint will have views to register 
# new users and to log in and log out

import functools
import pickle

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from howamidoing.objects import *
from howamidoing.db import get_db

# Create a Blueprint named 'auth'
bp = Blueprint('auth', __name__, url_prefix='/auth')

# ==============
# View: Register
# ==============

# /auth/register
@bp.route('/register', methods=('GET', 'POST'))
def register():
    # If the user submitted the form, request.method 
    # will be 'POST'. Start validating the input
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # Error Checking
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        # Input validation succeed. Initialize a new
        # profile and insert into the database. Catch
        # Integrity error for duplicate username.
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password, pickled_profile) VALUES (?, ?, ?)",
                    (
                        username, 
                        generate_password_hash(password),
                        pickle.dumps(Profile())
                    )
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                # url_for() generates the URL for the 
                # login view based on its name
                return redirect(url_for("auth.login"))

        # flash() stores messages that can be retrieved
        #  when rendering the template
        flash(error)

    return render_template('auth/register.html')

# ===========
# View: Login
# ===========

# /auth/login
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        # Query form database
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone() # returns one row from the query

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            # session is a dict that stores data across requests
            # When validation succeeds, the user’s id is 
            # stored in a new session
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


# bp.before_app_request() registers a function that 
# runs before the view function, no matter what URL is 
# requested
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


# ============
# View: Logout
# ============

# /auth/logout
@bp.route('/logout')
def logout():
    # session will no longer have 'user_id'
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    """Require Authentication in Other Views"""
    # This decorator returns a new view function 
    # that wraps the original view it’s applied to.
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view