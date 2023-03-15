from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from howamidoing.auth import login_required
from howamidoing.db import get_db

bp = Blueprint('profile', __name__)

@bp.route('/')
def index():
    if session.get("user_id") is not None: # Logged in
        try:
            course_details = g.profile.get_detail()
            return render_template('index.html', course_details = course_details)
        except Exception as e: # No courses
            return render_template('index.html', course_details = [])
    # Not Logged in
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
            # Create new course and set its status
            new_course = g.profile.add_course(corr=corr, name=name)
            new_course.set_status(status)

            # Update the user's profile in the database
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile._to_json()}})
            
            return redirect(url_for('index'))

    return render_template('profile/add_course.html')


@bp.route('/delete_course/<course_id>', methods=['GET'])
@login_required
def delete_course(course_id):
    users = get_db().users

    # Remove the course with the given ID from the user's profile
    g.profile.remove_course(course_id)

    # Update the user's profile in the database
    users.update_one(
        {'_id': g.user['_id']},
        {'$set': {'profile': g.profile._to_json()}}
    )

    # Return a redirect to the profile page
    return redirect(url_for('profile.index'))