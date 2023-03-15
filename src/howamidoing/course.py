from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from howamidoing.auth import login_required
from howamidoing.db import get_db

bp = Blueprint('course', __name__, url_prefix='/course')

@bp.route('/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_landing(course_id):
    # check if this course belongs to the logged in user
    if course_id not in g.profile.get_courses():
        return render_template('error.html', 
            message='You do not have permission to access this course.'
        ), 403


# @bp.route('/assignments/add')
# def add_assignment():
#     # your code here

# @bp.route('/assignments/edit/<int:assignment_id>')
# def edit_assignment(assignment_id):
#     # your code here

# @bp.route('/assignments/delete/<int:assignment_id>')
# def delete_assignment(assignment_id):
#     # your code here