from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from howamidoing.auth import login_required
from howamidoing.db import get_db

from .objects import Profile, Course

bp = Blueprint('course', __name__, url_prefix='/course')


def fetch_course(course_id : str) -> Course:
    """
    Check if this course belongs to the logged in user.
    Return None if check failed, else return the course
    object.
    """
    # Make sure course_id is string
    course_id = str(course_id)  
    profile : Profile = g.profile
    if course_id not in profile.get_courses():
        return None
    else:
        return profile.get_courses()[course_id]


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
        print(e)
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
        name = request.form['name']
        weight = float(request.form['weight'])
        score = float(request.form['score'])
        upper = float(request.form['upper'])
        users = get_db().users

        # Create new assignment
        course.add_uncurved_single(weight, score, name, upper)

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