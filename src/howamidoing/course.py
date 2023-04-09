from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from howamidoing.auth import login_required
from howamidoing.db import get_db
from howamidoing.objects import Profile, Course
from howamidoing.app_utils import fetch_course

bp = Blueprint('course', __name__, url_prefix='/course')


def validate_single_uncurved_assignment(form: dict):
    """
    Validate single uncurved assignment.
    Name, weight, score and upper should all have non empty
    values handled by html5.
    """
    # Error messages
    invalid_weight_message = "Weight of assignment should be a number between 0 and 1."
    invalid_score_message = "Score of assignment should be a number."
    invalid_upper_message = "Upper bound of assignment should be a number."

    # Validate weight
    try:
        weight = float(form['weight'])
        if weight > 1 or weight < 0:
            return False, invalid_weight_message
    except ValueError:
        return False, invalid_weight_message

    # Validate score
    try:
        float(form['score'])
    except ValueError:
        return False, invalid_score_message

    # Validate upper
    try:
        float(form['upper'])
    except ValueError:
        return False, invalid_upper_message

    return True, None


def validate_single_curved_assignment(form: dict):
    """
    Validate single curved assignment.
    Name, weight, score and upper should all have non empty
    values handled by html5.
    """
    # Validate fields that are also checked for
    # uncurved assignment
    is_valid, error = validate_single_uncurved_assignment(form)
    if not is_valid:
        return False, error
    
    # Error messages
    missing_mu_message = "You must enter a class average for a curved assignment. Grade estimations for curved classes depend on class average data."
    invalid_mu_message = "Class average of assignment should be a number"
    missing_sigma_message = "You must enter a class standard deviation for a curved assignment. Grade estimations for curved classes depend on class standard deviation data."
    invalid_sigma_message = "Class standard deviation of assignment should be a number."

    # Validate mu
    if form["mu"] is None:
        return False, missing_mu_message
    try:
        float(form['mu'])
    except ValueError:
        return False, invalid_mu_message
    
    # Validate sigma
    if form["sigma"] is None:
        return False, missing_sigma_message
    try:
        float(form['sigma'])
    except ValueError:
        return False, invalid_sigma_message
    
    return True, None


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


@bp.route('/<int:course_id>/components/add_single_assignment', methods=['GET', 'POST'])
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
        error = None

        # Added assignment is curved
        if request.form['curved'] == "Curved":
            
            # Validate form
            is_valid, error = validate_single_curved_assignment(request.form)

            # Flash error if not valid
            if not is_valid:
                flash(error, "error")

            # Fetch data from form and update profile
            else:
                name = request.form["name"]
                weight = float(request.form["weight"])
                score = float(request.form["score"])
                upper = float(request.form["upper"])
                mu = float(request.form["mu"])
                sigma = float(request.form["sigma"])

                course.add_curved_single(weight, score, name, upper, mu, sigma)

        # Added assignment is uncurved
        elif request.form['curved'] == "Not Curved":

            # Validate form
            is_valid, error = validate_single_uncurved_assignment(request.form)

            # Flash error if not valid
            if not is_valid:
                flash(error, "error")

            # Fetch data from form and update profile
            else:
                name = request.form["name"]
                weight = float(request.form["weight"])
                score = float(request.form["score"])
                upper = float(request.form["upper"])

                course.add_uncurved_single(weight, score, name, upper)

        # update the database if no error
        if error is None:
            # Update the user's profile in the database
            users.update_one(
                {"_id": g.user["_id"]},
                {"$set": {"profile": g.profile._to_json()}})
            
            return redirect(url_for('course.course_landing', course_id = course_id))

    return render_template('course/add_single_assignment.html')

# @bp.route('/assignments/edit/<int:assignment_id>')
# def edit_assignment(assignment_id):
#     # your code here

@bp.route('/<int:course_id>/components/delete/<int:component_id>', methods=['GET'])
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
        {'$set': {'profile': g.profile._to_json()}}
    )

    # Return a redirect to the profile page
    return redirect(url_for('course.course_landing', course_id = course_id))