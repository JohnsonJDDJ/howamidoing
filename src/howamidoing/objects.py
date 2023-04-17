from collections.abc import Iterable
from copy import deepcopy
from math import isclose
from scipy.stats import truncnorm
from typing import Union
from .utils import ID, generate_id, correlated_sigma_sum, Summary

class Assignment:
    """
    A generic assignment. The primary definition of an assignment
    is the score. If the assignment is graded on a curved basis, then
    it also must be defined by the mean (`mu`) and standard deviation
    (`sigma`). This class is inaccessible from user.

    Attributes
    ----------
    score : float
        The score earned on this assignment
    name : :obj:`str`, optional
        Name of this assignment. Optional
    upper : :obj:`float`, optional
        The maximum score available of this assignment. Defaults
        to 100.0
    mu : :obj:`float`, optional
        The mean of this assignment. Required for curved assignments.
    sigma : :obj:`float`, optional
        The standard deviation of this assignment. Required for
        curved assignments.
    curved : :obj:`bool`, optional
        Curved or not curved. Defaults to None. This attribute should
        not be accessible from user. 
    """

    def __init__(
        self, 
        score: float, 
        name: str = None,
        upper: float = 100, 
        mu: float = None,
        sigma: float = None,
        curved: bool = None,
        override_id: ID = None,
        override_json: dict = None
    ) -> None:

        # Overriding all steps using data from dictionary
        if override_json is not None:
            self._from_json(override_json)
            return

        self.id = ID(override_id) if override_id else generate_id(self) 
        self.name = name
        self.upper = upper
        
        if curved and (mu == None or sigma == None):
            raise ValueError("Curved assignment must have mean and standard deviation.")

        self.curved = curved
        self.mu = mu if mu else None
        self.sigma = sigma if sigma else None
        self.clobbered = False
        self.before_clobber = None

        # Curved assignment. Calculate z-score.
        if curved:
            self.score = score 
            self.zscore = (self.score - self.mu) / self.sigma
        # Un-curved assignment, zscore is 0.
        else:
            self.zscore = 0
            self.score = score 

        self.weight = None


    def __repr__(self) -> str:
        repr = f"Assignment {self.id}"
        if self.name: repr += f" ({self.name})"
        return f"<{repr}>"


    def _to_json(self) -> dict:
        """Convert all data to dictionary"""
        output = {
            "id" : self.id,
            "name" : self.name,
            "weight" : self.weight,
            "score" : self.score,
            "upper" : self.upper,
            "curved" : self.curved,
            "mu" : self.mu,
            "sigma" : self.sigma,
            "zscore" : self.zscore,
            "clobbered" : self.clobbered,
            "before_clobber" : self.before_clobber,
            "class" : "Assignment"
        }
        return output

    
    def _from_json(self, json: dict) -> None:
        """Load and override all data from dictionary"""
        self.id = ID(json["id"])
        self.name = json["name"]
        self.weight = json["weight"]
        self.score = json["score"]
        self.upper = json["upper"]
        self.curved = json["curved"]
        self.mu = json["mu"]
        self.sigma = json["sigma"]
        self.zscore = json["zscore"]
        self.clobbered = json["clobbered"]
        self.before_clobber = json["before_clobber"]


    def get_id(self) -> ID:
        """Return id"""
        return self.id

    
    def get_name(self) -> str:
        return self.name


    def get_score(self) -> float:
        """Return score"""
        return self.score

    
    def get_zscore(self) -> float:
        """Return zscore"""
        return self.zscore

    
    def get_primary_score(self) -> float:
        """
        Return score for uncurved assignments.
        Return zscore for curved assignments.
        """
        return self.zscore if self.curved else self.score

        
    def get_weight(self) -> float:
        """Return weight"""
        return self.weight

        
    def get_summary(self) -> Summary:
        """
        Return a dictionary of brief summaries about this
        assignment. Includes score and potentially the
        mean, standard deviation, and zscore of this 
        assignment if curved.
        """
        summary = Summary(
            self.score, 
            self.upper,
            self.zscore,
            self.mu,
            self.sigma)
        
        return summary

    
    def apply_clobber(self, zscore: float) -> None:
        # Revert to original if already clobbered
        if self.clobbered:
            self.revert_clobber()
        
        self.clobbered = True
        self.before_clobber = {
            "score": self.score,
            "zscore": self.zscore
        }
        self.zscore = zscore
        self.score = (self.zscore * self.sigma) + self.mu


    def revert_clobber(self) -> None:
        if not self.clobbered: return
        self.clobbered = False
        self.score = self.before_clobber["score"]
        self.zscore = self.before_clobber["zscore"]
        self.before_clobber = None


class CurvedSingleAssignment(Assignment):
    """
    A single curved assignment that count towards the final
    grade. Common assignments include exams and projects. 

    Attributes
    ----------
    weight : float
        The weight of this assignment counting toward the
        final grade
    score : float
        The score earned on this assignment
    name : :obj:`str`, optional
        Name of this assignment. Optional
    upper : :obj:`float`, optional
        The maximum score available of this assignment. Defaults
        to 100.0
    mu : float
        The mean of this assignment. Required for curved assignments.
    sigma : float
        The standard deviation of this assignment. Required for
        curved assignments.
    """

    def __init__(
        self, 
        weight: float, 
        score: float, 
        name: str = None, 
        upper: float = 100, 
        mu: float = None, 
        sigma: float = None,
        override_id: ID = None,
        override_json: dict = None
    ) -> None:
        if weight > 1.0 or weight <= 0: 
            raise ValueError(f"Invalid weight: {weight}.")
        super().__init__(score, name, upper, mu, sigma, True, override_id, override_json)
        # When override_json is used, weight will be a dummy
        # value. Thus only assign weight when override_json
        # is not used.
        if override_json is None:
            self.weight = weight


    def _to_json(self) -> dict:
        output = super()._to_json()
        output["class"] = "CurvedSingleAssignment"
        return output


class UncurvedSingleAssignment(Assignment):
    """
    A single uncurved assignment that counts toward the final
    grade. Common assignments include exams and projects. 
    
    Attributes
    ----------
    weight : float
        The weight of this assignment counting toward the
        final grade
    score : float
        The score earned on this assignment
    name : :obj:`str`, optional
        Name of this assignment. Optional
    upper : :obj:`float`, optional
        The maximum score available of this assignment. Defaults
        to 100.0
    """

    def __init__(
        self, 
        weight: float, 
        score: float, 
        name: str = None, 
        upper: float = 100,
        override_id : ID = None,
        override_json: dict = None
    ) -> None:
        if weight > 1.0 or weight <= 0: 
            raise ValueError(f"Invalid weight: {weight}.")
        super().__init__(score, name, upper, curved=False, override_id=override_id, override_json=override_json)
        # When override_json is used, weight will be a dummy
        # value. Thus only assign weight when override_json
        # is not used.
        if override_json is None:
            self.weight = weight


    def _to_json(self) -> dict:
        output = super()._to_json()
        output["class"] = "UncurvedSingleAssignment"
        return output


class AssignmentGroup:
    
    def __init__(
        self,
        weight: float,
        name: str = None, 
        corr: float = None,
        num_drops: int = 0,
        override_id: ID = None,
        override_json: dict = None
    ) -> None:
        # Overriding all step with data from dictionary
        if override_json is not None:
            self._from_json(override_json)
            return

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        self.id = ID(override_id) if override_id else generate_id(self)
        self.weight = weight
        self.name = name
        self.corr = corr
        self.curved = None
        self.num_drops = num_drops
        self.assignments : dict[ID, Assignment] = {} # {id : Assignment}


    def __repr__(self) -> str:
        repr = f"Assignment Group {self.id}"
        if self.name: repr += f" ({self.name})"
        return f"<{repr}>"

    
    def _to_json(self) -> dict:
        """Convert all data to dictionary"""
        assignments = {
            id: obj._to_json() for id, obj in self.get_assignments().items()
        }
        output = {
            "id" : self.id,
            "name" : self.name,
            "weight" : self.weight,
            "corr" : self.corr,
            "curved" : self.curved,
            "num_drops" : self.num_drops,
            "assignments" : assignments,
            "class" : "AssignmentGroup"
        }
        
        return output

    
    def _from_json(self, json: dict) -> None:
        """Load and override all data from dictionary"""
        self.id = ID(json["id"])
        self.name = json["name"]
        self.weight = json["weight"]
        self.corr = json["corr"]
        self.curved = json["curved"]
        self.num_drops = json["num_drops"]
        self.assignments = {}

        for id, sub_json in json["assignments"].items():
            # Only Assignment objects belong to AssignmentGroup
            assert sub_json["class"] == "Assignment"
            self.assignments[id] = Assignment(0, override_json=sub_json)


    def add_assignment(self) -> None:
        return NotImplementedError


    def get_id(self) -> ID:
        return self.id


    def get_name(self) -> str:
        return self.name
    

    def get_assignments(self) -> dict[ID, Assignment]:
        return self.assignments

    
    def get_weight(self) -> float:
        return self.weight


    def get_num_drops(self) -> int:
        return self.num_drops


    def _apply_drop(self) -> tuple[Iterable[Assignment], bool]:
        """Drop lowest scores according to self.num_drops"""
        assignments = list(self.assignments.values())
        # sort assignments according to primary score
        assignments.sort(key=lambda x: x.get_primary_score())
        # drop lowest num_drops assignments
        if len(assignments) > self.num_drops:
            assignments = assignments[self.num_drops:]
            drop_applied = True
        else:
            drop_applied = False

        return assignments, drop_applied
    

    def _calculate_summaries(self, assignments: Iterable[Assignment]) -> Summary:
        """Calculate the detail summary of assignments"""
        return NotImplementedError


    def get_summary(self) -> Summary:

        if len(self.assignments) == 0: raise AssertionError("No assignments in this group.")

        assignments, drop_applied = self._apply_drop()
        summary = self._calculate_summaries(assignments)
        summary["drop_applied"] = drop_applied

        return summary
    

    def get_detail(self) -> list:
        """
        AssignmentGroup detial is a list of assignment summaries
        """
        if len(self.assignments) == 0: raise AssertionError("No assignments in this group.")

        detail = []
        for id, assignment in self.get_assignments().items():
            summary = {"id" : id}
            summary["name"] = assignment.get_name()
            try:
                summary.update(assignment.get_summary().to_dict()) # Merge summary into info
            except Exception as e:
                summary["error_message"] = str(e)
            detail.append(summary)

        return detail
    

    def remove_assignment(self, assignment_id : ID) -> None:
        """
        Remove assignment with ID of ``assignment_id``.
        If such component does not exist, no-op.
        """
        if assignment_id in self.assignments:
            del self.assignments[assignment_id]



class CurvedAssignmentGroup(AssignmentGroup):
    """
    Each assignment in this group is curved and weighted equally. Assignents 
    with the lowest z-scores can be dropped due to policy. Even though
    rare, it is possible to apply clobber onto assignments.
    """
    
    def __init__(
        self, 
        weight: float, 
        name: str = None, 
        corr: float = 0.6, 
        num_drops: int = 0, 
        override_id : ID = None,
        override_json: dict = None
    ) -> None:
        super().__init__(weight, name, corr, num_drops, override_id, override_json)
        self.curved = True


    def _to_json(self) -> dict:
        output = super()._to_json()
        output["class"] = "CurvedAssignmentGroup"
        return output


    def add_assignment(self, score: float, name: str=None,
                       upper: float=100, mu: float=None, sigma: float=None,
                       override_id: ID = None) -> None:

        if name == None: name = "Assignment " + str(len(self.assignments) + 1)

        new_assignment = Assignment(score, name=name, 
                                    upper=upper, mu=mu, sigma=sigma, 
                                    curved=True, override_id=override_id)
        id = new_assignment.get_id()
        self.assignments[id] = new_assignment


    def _calculate_summaries(self, assignments: Iterable[Assignment]) -> Summary:
        """
        Calculate sums for score, mu and sigma. Then
        calculate zscore.
        """
        final_mu, final_sigma, final_score = 0, 0, 0

        for assignment in assignments:
            summary = assignment.get_summary()
            final_score += summary["_percentage"]
            final_mu += summary["_mu"]
            final_sigma = correlated_sigma_sum(
                final_sigma,
                summary["_sigma"],
                self.corr
            )

        final_zscore = (final_score - final_mu) / final_sigma

        summary = Summary(
            final_score,
            1.0,
            final_zscore,
            final_mu,
            final_sigma
        )

        return summary


class UncurvedAssignmentGroup(AssignmentGroup):
    """
    Each assignment in this group is curved and weighted equally. Assignents 
    with the lowest z-scores can be dropped due to policy. Even though
    rare, it is possible to apply clobber onto assignments.
    """
    
    def __init__(
        self, 
        weight: float, 
        name: str = None, 
        corr: float = None, 
        num_drops: int = 0, 
        override_id: ID = None,
        override_json: dict = None
    ) -> None:
        super().__init__(weight, name, corr, num_drops, override_id, override_json)
        self.curved = False


    def _to_json(self) -> dict:
        output = super()._to_json()
        output["class"] = "UncurvedAssignmentGroup"
        return output


    def add_assignment(self, score: float, name: str = None,
                       upper: float = 100, override_id: ID = None) -> None:

        if name == None: name = "Assignment " + str(len(self.assignments) + 1)

        new_assignment = Assignment(score, name=name, upper=upper, curved=False, 
                                    override_id=override_id)
        id = new_assignment.get_id()
        self.assignments[id] = new_assignment
        

    def _calculate_summaries(self, assignments: Iterable[Assignment]) -> Summary:
        """Calculate sums for score and upper"""
        final_score = 0

        for assignment in assignments:
            final_score += assignment.get_summary()["_percentage"]

        summary = Summary(final_score, 1.0)

        return summary


Component = Union[
    CurvedAssignmentGroup, 
    UncurvedAssignmentGroup,
    CurvedSingleAssignment,
    UncurvedSingleAssignment
]


class Course:
    """
    A course. Comprised of a list of assignments and/or assignment groups
    that have defined weights that add up to 100%. Each component of
    the final grade could be graded on absolute score or on a curved
    basis. The correlation of each assignment is adjustable. 

    Attributes
    ----------
    corr : float
        The correlation coefficient with regards to each pair of
        assignments. Defaults to 0.6, and could be adjusted higher
        for a stronger correlation or vice versa. `corr = 0` is 
        equivalent of assuming independence between each assignments.
    name : :obj:`str`, optional
        Name of this course. Defaults to 'My Course'.
    """

    _allowed_status = {
        "In Progress", 
        "Completed",
        "Other"
    }

    def __init__(
        self, 
        corr: float = 0.6, 
        name: str = None,
        override_id: ID = None,
        override_json: dict = None
    ) -> None:
        # Overriding all step with data from dictionary
        if override_json is not None:
            self._from_json(override_json)
            return

        if corr < 0 or corr > 1.0: raise ValueError(f"Invalid correlation coefficient: {corr}.")

        self.id = ID(override_id) if override_id else generate_id(self)
        self.corr = corr
        self.name = name if name else "My Course"
        self.status = "Other"
        self.components : dict[ID, dict] = dict() # {id, component_info_dict}
        self.clobber_info = None

        self.uncurved_boundaries = {
            "A+" : 0.97,
            "A" : 0.93,
            "A-" : 0.9,
            "B+" : 0.87,
            "B" : 0.83,
            "B-" : 0.8,
            "C+" : 0.77,
            "C" : 0.73,
            "C-" : 0.7,
            "D+" : 0.67,
            "D" : 0.63,
            "D-" : 0.6,
            "F" : 0.0
        }
        
        self.curved_boundaries = {
            "A+" : 0.95,
            "A" : 0.77,
            "A-" : 0.65,
            "B+" : 0.45,
            "B" : 0.30,
            "B-" : 0.20,
            "C+" : 0.15,
            "C" : 0.10,
            "C-" : 0.07,
            "D+" : 0.05,
            "D" : 0.04,
            "D-" : 0.03,
            "F" : 0.0
        }


    def __repr__(self) -> str:
        repr = f"Course {self.id}"
        if self.name: repr += f" ({self.name})"
        return f"<{repr}>"


    def _to_json(self) -> dict:
        """Convert all data to dictionary"""
        components = deepcopy(self.components)
        for info in components.values():
            info["object"] = info["object"]._to_json()

        output = {
            "id" : self.id,
            "name" : self.name,
            "corr" : self.corr,
            "status" : self.status,
            "clobber_info" : self.clobber_info,
            "uncurved_boundaries" : self.uncurved_boundaries,
            "curved_boundaries": self.curved_boundaries,
            "components" : components,
            "class" : "Course"
        }

        return output


    def _from_json(self, json: dict) -> None:
        """Load and override all data from dictionary"""
        self.id = ID(json["id"])
        self.name = json["name"]
        self.corr = json["corr"]
        self.status = json["status"]
        self.clobber_info = json["clobber_info"]
        self.uncurved_boundaries = json["uncurved_boundaries"]
        self.curved_boundaries = json["curved_boundaries"]

        # A dict of allowed class and convenient instantiation
        allowed_classes = {
            "CurvedAssignmentGroup": CurvedAssignmentGroup,
            "UncurvedAssignmentGroup": UncurvedAssignmentGroup,
            "CurvedSingleAssignment": CurvedSingleAssignment,
            "UncurvedSingleAssignment": UncurvedSingleAssignment
        }

        for info in json["components"].values():
            obj_class = info["object"]["class"]
            assert obj_class in allowed_classes
            # Use dummy class attributes to create instances
            obj = allowed_classes[obj_class](0.5, 5, override_json=info["object"])
            info["object"] = obj

        self.components = json["components"]
            
 
    def get_id(self) -> ID:
        """Return id"""
        return self.id

    
    def get_name(self) -> str:
        """Return name"""
        return self.name


    def get_components(self) -> dict[ID, dict]:
        return self.components


    def get_status(self) -> str:
        return self.status


    def set_status(self, status: str) -> None:
        if status in self._allowed_status:
            self.status = status
        else:
            raise ValueError("Invalid status.")


    def _calculate_curved_info(
        self, 
        assignments: Iterable[Component]
    ) -> dict[str, float]:
        """
        Calculate weighted score, mu, sigma and zscore 
        for curved components as a dictionary
        """
        curved = {
            "score": 0,
            "upper": 0,
            "mu": 0,
            "sigma": 0,
            "zscore": 0,
            "curved": False
        }

        if len(assignments) == 0: 
            return curved
        else:
            curved["curved"] = True

        for component in assignments:
            summary = component.get_summary()
            curved["score"] += summary["_percentage"] * component.get_weight()
            curved["mu"] += summary["_mu"] * component.get_weight()
            curved["sigma"] = correlated_sigma_sum(
                curved["sigma"],
                summary["_sigma"] * component.get_weight(),
                self.corr
            )
        curved["zscore"] = (curved["score"] - curved["mu"]) / curved["sigma"]

        return curved


    def _calculate_uncurved_info(
        self,
        assignments: Iterable[Component]
    ) -> dict[str, float]:
        """
        Calculate weighted score for uncurved components
        as a dictionary
        """
        uncurved = {"score": 0}
        for component in assignments:
            summary = component.get_summary()
            uncurved["score"] += summary["_percentage"] * component.get_weight()
        return uncurved


    def _calculate_summary(
        self,
        curved: Iterable[Component],
        uncurved: Iterable[Component],
        total_weight: float
    ) -> Summary:
        """
        Calculte weighted scores, mu, sigma and zscore for
        all assignments. Then estimate the letter grade.
        """
        # Combine everthing
        curved_info = self._calculate_curved_info(curved)
        uncurved_info = self._calculate_uncurved_info(uncurved)

        overall_score = curved_info["score"] + uncurved_info["score"]
        final_score = overall_score / total_weight

        overall_mu = curved_info["mu"] + uncurved_info["score"]
        final_mu = overall_mu / total_weight

        final_sigma = curved_info["sigma"] / total_weight
        
        if curved_info["curved"]:
            summary = Summary(
                final_score, 
                1.0,
                curved_info["zscore"], 
                final_mu,
                final_sigma)
        else:
            summary = Summary(final_score, 1.0)

        return summary

    def _get_grade(self, summary : Summary, show_boundary=False) -> str:
        """Calclate the letter grade for ths course"""
        # Calculate letter grade using scipy.stat.truncnorm
        if summary["class_curved"]:
            a = (0 - summary["_mu"]) / summary["_sigma"]
            b = (1 - summary["_mu"]) / summary["_sigma"]
            X = truncnorm(a, b, loc=summary["_mu"], scale=summary["_sigma"])
            true_boundaries = {
                k: X.ppf(v) for k,v in self.curved_boundaries.items()
            }
        else:
            true_boundaries = self.uncurved_boundaries
        
        if show_boundary:
            print("Letter grade boundaries:")
            print(true_boundaries)

        for k, v in true_boundaries.items():
            letter_grade = k
            if summary["_percentage"] >= v:
                break
        
        return letter_grade


    def get_summary(self) -> Summary:
        """
        Overall statistics of the course
        """
        # Error checking
        if len(self.components) == 0:
            raise AssertionError("No components in this course. Click on the bottons to the right to enter and add new components.")
    
        # Iterate over components:
        # Classify into curved and uncurved.
        # Compute the total weight.
        total_weight, curved, uncurved = 0, [], []
        for component in self.components.values():
            if component["curved"]: 
                curved.append(component["object"])
            else: uncurved.append(component["object"])
            total_weight += component["weight"]
            if total_weight > 1.0: raise ValueError("Total weight exceeds one.")
        
        # Check if the weights are incomplete
        is_final = isclose(total_weight, 1.0)

        summary = self._calculate_summary(curved, uncurved, total_weight)        
        summary["class_curved"] = bool(len(curved))
        summary["is_final"] = is_final

        # Estimate letter grade
        summary["grade"] = self._get_grade(summary)
        
        return summary


    def get_detail(self) -> list:
        """
        Course detail is a list of component info that includes summaries.
        """
        if len(self.components) == 0:
            raise AssertionError("No components yet!")

        detail = []
        for id, old_component_info in self.components.items():
            component_info = {"id" : id}
            component_info.update(old_component_info) # Merge two dictionary
            component : Component = component_info["object"] 
            component_info["name"] = component.get_name()
            del component_info["object"] # Remove object field
            try:
                component_info.update(component.get_summary().to_dict()) # Merge summary into info
            except Exception as e:
                component_info["error_message"] = str(e)
            detail.append(component_info)

        # Sort by weight
        detail.sort(key = lambda component_summary: component_summary["weight"], reverse=True)

        return detail


    def add_curved_single(self, weight: float, score: float, name: str = None,
                          upper: float = 100, mu: float = None, sigma: float = None,
                          override_id : ID = None
                          ) -> CurvedSingleAssignment:

        if name == None: name = "Assignment " + str(len(self.components) + 1)
        new_component = CurvedSingleAssignment(
            weight, score, name, upper, mu, sigma, override_id=override_id
        )
        id = new_component.get_id()

        info = {
            "curved": True,
            "weight": weight,
            "grouped": False,
            "object": new_component
        }

        self.components[id] = info
        return new_component
    

    def add_uncurved_single(self, weight: float, score: float, name: str = None, 
                            upper: float = 100, override_id: ID = None) -> UncurvedSingleAssignment:
        if name == None: name = "Assignment " + str(len(self.components) + 1)
        new_component = UncurvedSingleAssignment(
            weight, score, name, upper, override_id=override_id
        )
        id = new_component.get_id()

        info = {
            "curved": False,
            "weight": weight,
            "grouped": False,
            "object": new_component
        }

        self.components[id] = info
        return new_component


    def add_curved_group(
        self, 
        weight: float, 
        name: str = None,
        corr: float = None, 
        num_drops: int = 0,
        override_id: ID = None
    ) -> CurvedAssignmentGroup:
        if corr == None: corr = self.corr
        if name == None: name = "Grouped Assignments " + str(len(self.components) + 1)
        new_component = CurvedAssignmentGroup(weight, name, corr, num_drops, override_id=override_id)
        id = new_component.get_id()

        info = {
            "curved": True,
            "weight": weight,
            "grouped": True,
            "object": new_component
        }

        self.components[id] = info
        return new_component


    def add_uncurved_group(
        self, 
        weight: float, 
        name: str = None, 
        corr: float = None,
        num_drops: int = 0,
        override_id: ID = None
    ) -> UncurvedAssignmentGroup:    
        if name == None: name = "Grouped Assignments " + str(len(self.components) + 1)
        new_component = UncurvedAssignmentGroup(weight, name, corr, num_drops, override_id=override_id)
        id = new_component.get_id()

        info = {
            "curved": False,
            "weight": weight,
            "grouped": True,
            "object": new_component
        }

        self.components[id] = info
        return new_component

    
    def apply_clobber(
        self, source: ID, 
        targets: list[ID], 
        capacity: int = -1
    ) -> None:
        # Check for errors:
        #  - Other clobber already applied: revert automatically
        #  - Source in targets
        #  - Assignemnt not in self.components
        #  - Assignment not curved
        #  - Assignment is grouped
        if self.clobber_info is not None:
            self.revert_clobber()

        if source in targets: raise ValueError("Source assignment cannot be in targets.")

        if source not in self.components.keys(): raise ValueError("Source assignment not found.")
        elif not self.components[source]["curved"]: raise ValueError("Source assignment is not curved.")
        elif self.components[source]["grouped"]: raise ValueError("Source assignment must be single not grouped.")

        for i, target in enumerate(targets):
            if target not in self.components.keys(): raise ValueError(f"Target assignment at index {i} not found")
            elif not self.components[target]["curved"]: raise ValueError(f"Target assignment at index {i} is not curved.")
            elif self.components[target]["grouped"]: raise ValueError(f"Target assignment at index {i} must be single not grouped.")

        if capacity == -1: capacity = len(targets)
        def argmin(iterable):
            return min(enumerate(iterable), key=lambda x: x[1])[0]

        # Convert id into objects
        source = self.components[source]["object"]
        targets = [self.components[target]["object"] for target in targets]
        
        # Fetch the zscores for clobbering
        z_source = source.get_zscore()
        z_targets = [target.get_zscore() for target in targets]
        clobbered_components = []    
        
        # Apply clobber while we have capacity
        while capacity != 0:
            # Zscore from source is no longer larger than any zscore from targets
            # Stop applying clobber
            if all([z_source <= z for z in z_targets]): break

            # Find the index of the assignment with minimum zscore.
            # Pop that assignment from the targets list and apply clobber
            min_index = argmin(z_targets)
            min_assignment = targets.pop(min_index)
            del z_targets[min_index]

            min_assignment.apply_clobber(z_source)
            clobbered_components.append(min_assignment.get_id())

            capacity -= 1
        
        self.clobber_info = {
            "source": source.get_id(),
            "targets": clobbered_components
        }


    def revert_clobber(self) -> None:
        if self.clobber_info is not None:   
            for component in self.clobber_info["targets"]:
                component = self.components[component]["object"]
                component.revert_clobber()
        self.clobber_info = None

    
    def remove_component(self, component_id: ID) -> None:
        """
        Remove component with ID of ``component_id``.
        If such component does not exist, no-op.
        """
        # Revert clobber before removing components
        self.revert_clobber()
        if component_id in self.components:
            del self.components[component_id]


class Profile():
    """
    A user's profile is a container for `Courses`. This object
    is used for packaging a user's data. The profile
    is at the top of the hierarchy for objects related to 
    `howamidoing`.
    """

    
    def __init__(self, override_json: dict = None) -> None:
        self.courses : dict[ID, Course] = {}
        if override_json is not None:
            self.from_json(override_json)
            

    def __repr__(self) -> str:
        return self.courses.__repr__()

    
    def __getitem__(self, key: ID) -> Course:
        return self.courses[key]


    def __delitem__(self, key: ID) -> None:
        del self.courses[key]

    
    def to_json(self) -> dict:
        output = deepcopy(self.courses)
        for id, course in output.items():
            output[id] = course._to_json()
        return output
    
    def from_json(self, json: dict) -> None:
        self.courses = {}
        for id, course_json in json.items():
            self.courses[id] = Course(override_json=course_json)


    def get_courses(self) -> dict[ID, Course]:
        return self.courses

    
    def get_detail(self) -> list:
        """
        Profile detail is a list of course info that includes summaries.
        """
        if len(self.courses) == 0:
            raise AssertionError("No courses yet! Add your courses now and track your performance.")

        detail = []
        for id, course in self.courses.items():
            course_info = {"id" : id}
            course_info["name"] = course.get_name()
            course_info["status"] = course.get_status()
            try:
                course_info.update(course.get_summary().to_dict())
            except Exception as e:
                course_info["error_message"] = str(e)
            detail.append(course_info)

        # Sort by status
        status_ordering = {"In Progress": 0, "Other": 1, "Completed": 2}
        detail.sort(key = lambda course_info: status_ordering[course_info["status"]])

        return detail
    

    def add_course(
            self, 
            corr: float = 0.6, 
            name: str = None
        ) -> Course:
        """Create a new course"""
        if name is None: name = "Course " + str(len(self.courses) + 1)
        new_course = Course(corr, name)
        self.courses[new_course.get_id()] = new_course
        return new_course


    def remove_course(
            self, 
            course_id : ID
        ) -> None:
        """
        Remove a course by its id. Does nothing if course
        not exist. Returns nothing.
        """
        del self.courses[course_id]