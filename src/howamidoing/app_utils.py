from flask import g
from howamidoing.objects import (
    Course, Profile, Component, UncurvedAssignmentGroup, CurvedAssignmentGroup, Assignment
)
from howamidoing.utils import ID
from typing import Union


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
    
    
def fetch_component(
        course : Course, 
        component_id : ID, 
        group_only : bool = False
        ) -> Component:
    """
    Check if this component belongs to the course. It does not
    check whether the course belongs to the logged in user so
    always run fetch_course() before running fetch_component().

    Return None if check failed, else return the component
    object.
    """
    # Make sure component_id is ID
    component_id = ID(component_id)
    components_info = course.get_components()
    if component_id not in components_info:
        return None
    elif group_only and not components_info[component_id]["grouped"]:
        return None
    else:
        return components_info[component_id]["object"]
    

def fetch_grouped_assignment(
        group : Union[UncurvedAssignmentGroup, CurvedAssignmentGroup],
        assignment_id: ID
    ) -> Assignment:
    """
    Check if the assignment belong to the group. It does not
    check whether the group belongs to the logged in user so
    always run fetch_course() AND fetch_component() before running 
    fetch_component().

    Return None if check failed, else return the component
    object.
    """
    # Make sure component_id is ID
    assignment_id = ID(assignment_id)

    if assignment_id not in group.get_assignments():
        return None
    else:
        return group.get_assignments()[assignment_id]
    

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


def validate_single_assignment(form: dict, curved: bool):
    """
    Validate single assignment, both curved and uncurved.
    Name, weight, score and upper should all have non empty
    values handled by html5.
    """
    # Error messages
    invalid_weight_message = "Weight of assignment should be a number between 0 and 1."
    invalid_score_message = "Score of assignment should be a number."
    invalid_upper_message = "Upper bound of assignment should be a number."
    missing_mu_message = "You must enter a class average for a curved assignment. Grade estimations for curved classes depend on class average data."
    invalid_mu_message = "Class average of assignment should be a number"
    missing_sigma_message = "You must enter a class standard deviation for a curved assignment. Grade estimations for curved classes depend on class standard deviation data."
    invalid_sigma_message = "Class standard deviation of assignment should be a number."

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
    
    if curved:
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


def validate_assignment_group(form: dict):
    """
    Validate assignment group.
    Name, weight, corr and num_drops should all have non empty
    values handled by html5.
    """
    # Error messages
    invalid_weight_message = "Weight of this assignment group should be a number between 0 and 1."
    invalid_corr_message = "Correlation coefficient must be a number between 0 and 1."
    invalid_num_drops_message = "The number of drops should be an integer greater or equal to 0."

    # Validate weight
    try:
        weight = float(form['weight'])
        if weight > 1 or weight < 0:
            return False, invalid_weight_message
    except ValueError:
        return False, invalid_weight_message
    
    # Validate corr
    try:
        corr = float(form['corr'])
        if corr < 0 or corr > 1:
            return False, invalid_corr_message
    except ValueError:
        return False, invalid_corr_message

    # Validate num_drops
    try:
        num_drops = int(form['num_drops'])
        if num_drops < 0:
            return False, invalid_num_drops_message
    except ValueError:
        return False, invalid_num_drops_message
    
    return True, None


def validate_group_assignment(form: dict, curved: bool):
    """
    Validate assignment within a group.
    Name, score, upper (possibly mu, sigma) should all have non empty
    values handled by html5.
    """
    # Error messages
    invalid_score_message = "Score of assignment should be a number."
    invalid_upper_message = "Upper bound of assignment should be a number."
    missing_mu_message = "You must enter a class average for a curved assignment. Grade estimations for curved classes depend on class average data."
    invalid_mu_message = "Class average of assignment should be a number"
    missing_sigma_message = "You must enter a class standard deviation for a curved assignment. Grade estimations for curved classes depend on class standard deviation data."
    invalid_sigma_message = "Class standard deviation of assignment should be a number."

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
    
    if curved:
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


def create_single_assignment_from_form(
        course: Course, 
        form: dict, 
        component_id: ID = None
    ):
    """
    Add the single assignment from the request form to 
    user's profile. 
    
    If ``component_id`` is specified, then
    remove any component in the course with the same
    id, create a new single assignment object and explicitly
    set the id for the newly created object.

    Else, create a new single assignment object with its generic
    id. 
    """
    # Make sure component_id is ID
    if component_id is not None:
        component_id = ID(component_id)
        
    # Validate form
    curved = form['curved'] == "Curved"
    is_valid, error = validate_single_assignment(form, curved=curved)

    # Return error if not valid
    if not is_valid:
        return error

    # Fetch data from form and update profile
    name = form["name"]
    weight = float(form["weight"])
    score = float(form["score"])
    upper = float(form["upper"])
    if curved:
        mu = float(form["mu"])
        sigma = float(form["sigma"])

    # Remove existing assignment if specified
    if component_id is not None:
        course.remove_component(component_id)
    
    # Add the assignment to user's profile
    if curved:
        course.add_curved_single(weight, score, name, upper, mu, sigma, override_id=component_id)
    else:
        course.add_uncurved_single(weight, score, name, upper, override_id=component_id)

    return None


def create_assignment_group_from_form(
        course: Course, 
        form: dict, 
        component_id: ID = None
    ):
    """
    Add the assignment group from the request form to 
    user's profile. 
    
    If ``component_id`` is specified, then fetch the
    group with the specified id and edit the existing group.

    Note: If editing the group changes the type between curved
    and uncurved, then all assignments within the group will be 
    removed.

    Else, create a new assignment group object with its generic
    id. 
    """
    # Validate form
    is_valid, error = validate_assignment_group(form)

    # Return error if not valid
    if not is_valid:
        return error

    # Fetch data from form and update profile
    name = form["name"]
    weight = float(form["weight"])
    curved = form["curved"] == "Curved"
    corr = float(form["corr"])
    num_drops = int(form["num_drops"])

    # [Edit] the existing group
    # Make sure component_id is ID
    if component_id is not None:
        component_id = ID(component_id)
        # fetch and edit the existing group
        group = course.get_components()[component_id]["object"]

        # If "curved" from form is different form itself, 
        # trash the old group and build a new group.
        if curved != group.curved:
            course.remove_component(component_id)
            if curved:
                course.add_curved_group(weight, name, corr, num_drops)
            else:
                course.add_uncurved_group(weight, name, corr, num_drops)
        else:
            # Edit in place
            group.name = name
            group.weight = weight
            group.corr = corr
            group.num_drops = num_drops

    # [Add] the group to user's profile
    else:
        if curved:
            course.add_curved_group(weight, name, corr, num_drops)
        else:
            course.add_uncurved_group(weight, name, corr, num_drops)

    return None


def create_group_assignment_from_form(
        group : Union[UncurvedAssignmentGroup, CurvedAssignmentGroup],
        form : dict,
        assignment_id : ID = None
    ):
    """
    Add the assignment from the request form to the
    assignment group and to the user's profile
    
    If ``assignment_id`` is specified, then
    remove any assignment in the course with the same
    id, create a new assignment object and explicitly
    set the id for the newly created object.

    Else, create a new assignment object with its generic
    id. 
    """
    # Make sure assignment_id is ID
    if assignment_id is not None:
        assignment_id = ID(assignment_id)
 
    # Validate form
    is_valid, error = validate_group_assignment(form, curved = group.curved)

    # Return error if not valid
    if not is_valid:
        return error

    # Fetch data from form and update profile
    name = form["name"]
    score = float(form["score"])
    upper = float(form["upper"])

    # Also fetch class stats for curved group
    if group.curved:
        mu = float(form["mu"])
        sigma = float(form["sigma"])

    # Remove existing assignment if specified
    if assignment_id is not None:
        group.remove_assignment(assignment_id)

    # Add the assignment to user's profile
    if group.curved:
        group.add_assignment(score, name, upper, mu, sigma, override_id=assignment_id)
    else:
        group.add_assignment(score, name, upper, override_id=assignment_id)

    return None