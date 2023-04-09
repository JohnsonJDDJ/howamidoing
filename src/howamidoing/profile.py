from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from howamidoing.auth import login_required
from howamidoing.db import get_db
from howamidoing.app_utils import fetch_course, validate_course

bp = Blueprint('profile', __name__)


@bp.route('/')
def index():
    """
    Home page
    Will display differently depends on login status
    """
    # Logged in
    if session.get("user_id") is not None:
        try:
            profile_details = g.profile.get_detail()
            return render_template('index.html', profile_details = profile_details)
        # Logged in but no courses -> profile_details = []
        except Exception as e: 
            return render_template('index.html', profile_details = [])
    # Not Logged in
    return render_template('index.html', profile_details = [])


@bp.route('/add_course', methods=('GET', 'POST'))
@login_required
def add_course():
    if request.method == 'POST':
        # Get db
        users = get_db().users
        error = None

        # Validate form
        is_valid, error = validate_course(request.form)
        if not is_valid:
            flash(error)
        else:
            name = request.form['name']
            corr = float(request.form['corr'])
            status = request.form['status']

            # Create new course and set its status
            new_course = g.profile.add_course(corr=corr, name=name)
            new_course.set_status(status)

            # Update the user's profile in the database
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile._to_json()}})
            
            return redirect(url_for('index'))

    return render_template('profile/add_course.html')


@bp.route('/edit_course/<int:course_id>', methods=('GET', 'POST'))
@login_required
def edit_course(course_id):
    # Get db
    users = get_db().users

    # check if this course belongs to the logged in user
    course = fetch_course(course_id)
    if course is None:
        return render_template('error.html', 
            message = 'You do not have permission to access this course.'
        ), 403

    if request.method == 'POST':
        # Validate form
        is_valid, error = validate_course(request.form)
        if not is_valid:
            flash(error)
        else:
            # Update course information
            course.name = request.form['name']
            course.corr = float(request.form['corr'])
            course.set_status(request.form['status'])

            # Update the user's profile in the database
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile._to_json()}})
            
            return redirect(url_for('index'))

    return render_template('profile/edit_course.html', course = course)



@bp.route('/delete_course/<course_id>', methods=['GET'])
@login_required
def delete_course(course_id):
    # check if this course belongs to the logged in user
    course = fetch_course(course_id)
    if course is None:
        return render_template('error.html', 
            message = 'You do not have permission to access this course.'
        ), 403

    # Remove the course with the given ID from the user's profile
    g.profile.remove_course(course_id)

    # Update the user's profile in the database
    users = get_db().users
    users.update_one(
        {'_id': g.user['_id']},
        {'$set': {'profile': g.profile._to_json()}}
    )

    # Return a redirect to the profile page
    return redirect(url_for('profile.index'))