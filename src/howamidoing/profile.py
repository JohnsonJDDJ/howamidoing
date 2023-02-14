from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from howamidoing.auth import login_required
from howamidoing.db import get_db

bp = Blueprint('profile', __name__)

@bp.route('/')
def index():
    if session.get("user_id") is not None: # Not logged in
        try:
            course_details = g.profile.get_detail()
            return render_template('index.html', course_details = course_details)
        except Exception as e: # No courses
            return render_template('index.html', course_details = [])
    return render_template('index.html', course_details = [])


@bp.route('/add_course', methods=('GET', 'POST'))
@login_required
def add_course():
    if request.method == 'POST':
        name = request.form['name']
        corr = float(request.form['corr'])
        status = request.form['status']
        users = get_db().users
        error = None

        if not name:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            new_course = g.profile.add_course(corr=corr, name=name)
            new_course.set_status(status)
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile._to_json()}})
            return redirect(url_for('index'))

    return render_template('profile/add_course.html')