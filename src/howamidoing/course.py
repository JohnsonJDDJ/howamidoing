from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from howamidoing.auth import login_required
from howamidoing.db import get_db
from howamidoing.objects import Profile, Course
from howamidoing.app_utils import (
    fetch_course, fetch_component, create_single_assignment_from_form
)

bp = Blueprint('course', __name__, url_prefix='/course')


@bp.route('/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_landing(course_id):
    # check if this course belongs to the logged in user
    course = fetch_course(course_id)
    if course is None:
        return render_template('error.html', 
            message = 'You do not have permission to access this course.'
        ), 403
    
    # display course detail
    try:
        course_details = course.get_detail()
        return render_template('course.html', course = course, course_details = course_details)
    # no components -> course_details = []
    except Exception as e: 
        return render_template('course.html', course = course, course_details = [])


@bp.route('/<int:course_id>/add_single_assignment', methods=['GET', 'POST'])
@login_required
def add_single_assignment(course_id):
    # check if this course belongs to the logged in user
    course = fetch_course(course_id)
    if course is None:
        return render_template('error.html', 
            message = 'You do not have permission to access this course.'
        ), 403
    
    if request.method == 'POST':
        # Get db
        users = get_db().users

        # Create the assignment from form
        error = create_single_assignment_from_form(course, request.form)

        # Flash error
        if error is not None:
            flash(error)

        # update the database if no error
        else:
            # Update the user's profile in the database
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile.to_json()}})
            
            return redirect(url_for('course.course_landing', course_id = course_id))

    return render_template('course/add_single_assignment.html')


@bp.route('/<int:course_id>/edit_single_assignment/<int:component_id>', methods=['GET', 'POST'])
@login_required
def edit_single_assignment(course_id, component_id):
    # check if this course belongs to the logged in user
    course = fetch_course(course_id)
    if course is None:
        return render_template('error.html', 
            message = 'You do not have permission to access this course.'
        ), 403
    
    # check if this component exist
    assignment = fetch_component(course, component_id)
    if assignment is None:
        return render_template('error.html', 
            message = f'Assignment not found with given id: {component_id}.'
        ), 404

    if request.method == 'POST':
        # Get db
        users = get_db().users

        # Create the assignment from form
        error = create_single_assignment_from_form(course, request.form, component_id=component_id)

        # Flash error
        if error is not None:
            flash(error)

        # update the database if no error
        else:
            # Update the user's profile in the database
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile.to_json()}})
            
            return redirect(url_for('course.course_landing', course_id = course_id))

    return render_template('course/edit_single_assignment.html', assignment = assignment)


@bp.route('/<int:course_id>/delete/<int:component_id>', methods=['GET'])
@login_required
def delete_component(course_id, component_id):
    # check if this course belongs to the logged in user
    course = fetch_course(course_id)
    if course is None:
        return render_template('error.html', 
            message = 'You do not have permission to access this course.'
        ), 403
    
    users = get_db().users

    # Remove the course with the given ID from the user's profile
    course.remove_component(str(component_id))

    # Update the user's profile in the database
    users.update_one(
        {'_id': g.user['_id']},
        {'$set': {'profile': g.profile.to_json()}}
    )

    # Return a redirect to the profile page
    return redirect(url_for('course.course_landing', course_id = course_id))