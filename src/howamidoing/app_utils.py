from flask import g
from howamidoing.objects import Course, Profile, Component
from howamidoing.utils import ID


def fetch_course(course_id : ID) -> Course:
    """
    Check if this course belongs to the logged in user.
    Return None if check failed, else return the course
    object.
    """
    # Make sure course_id is ID
    course_id = ID(course_id)  
    profile : Profile = g.profile
    if course_id not in profile.get_courses():
        return None
    else:
        return profile.get_courses()[course_id]
    
    
def fetch_component(course : Course, component_id : ID) -> Component:
    """
    Check if this component belongs to the course. It does not
    check whether the course belongs to the logged in user so
    always run fetch_course() before running fetch_component().
    Return None if check failed, else return the component
    object.
    """
    # Make sure component_id is a string
    component_id = ID(component_id)
    components_info = course.get_components()

def validate_course(form):
    """
    Validate course.
    Name, status, and corr should all have non empty
    values handled by html5.
    """
    invalid_corr_message = "Correlation coefficient must be a number between 0 and 1."
    # Validate corr
    try:
        corr = float(form['corr'])
        if corr < 0 or corr > 1:
            return False, invalid_corr_message
    except ValueError:
        return False, invalid_corr_message

    return True, None


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