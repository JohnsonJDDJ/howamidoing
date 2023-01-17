from collections.abc import Iterable
from math import isclose
from scipy.stats import truncnorm
from typing import Union
from .utils import *

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
        curved: bool = None
    ) -> None:

        self.id = generate_id(self)
        self.name = name
        self.upper = upper
        
        if curved and (mu == None or sigma == None):
            raise ValueError("Curved assignment must have mean and standard deviation.")

        self.curved = curved
        self.mu = mu / self.upper if mu else None
        self.sigma = sigma / self.upper if sigma else None
        self.clobbered = False
        self.before_clobber = None

        # Curved assignment. Calculate z-score.
        if curved:
            self.score = score / self.upper
            self.zscore = (self.score - self.mu) / self.sigma
        # Un-curved assignment, zscore is 0.
        else:
            self.zscore = 0
            self.score = score / self.upper

        self.weight = None # Undefined in this class


    def get_id(self) -> int:
        """Return id"""
        return self.id


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

        
    def get_detail(self) -> dict:
        """
        Return a dictionary of full details about this
        assignment. Includes score and potentially the
        mean, standard deviation, and zscore of this 
        assignment if curved.
        """
        detail = dict()
        detail["score"] = self.score
        # For uncurved assignment, do not pass in
        # any other stats except the score.
        if not self.curved:
            detail["stats"] = dict()
        else:
            detail["stats"] = {
                "zscore" : self.zscore,
                "mu" : self.mu,
                "sigma" : self.sigma
            }
        return detail

    
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
        sigma: float = None
        ) -> None:

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        super().__init__(score, name, upper, mu, sigma, curved=True)
        self.weight = weight


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
        upper: float = 100
    ) -> None:

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        super().__init__(score, name, upper, curved=False)
        self.weight = weight


class AssignmentGroup:
    
    def __init__(
        self,
        weight: float,
        name: str = None, 
        num_drops: int = 0
    ) -> None:

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        self.id = generate_id(self)
        self.assignments = dict()
        self.weight = weight
        self.name = name
        self.num_drops = num_drops


    def add_assignment(self) -> None:
        return NotImplementedError


    def get_id(self) -> int:
        return self.id

    
    def get_assignments(self) -> dict[int, Assignment]:
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
    

    def _calculate_details(self, assignments: Iterable[Assignment]) -> dict:
        """Calculate the summary detail of assignments"""
        return NotImplementedError


    def get_detail(self) -> dict:

        if len(self.assignments) == 0: raise AssertionError("No assignments in this group.")

        assignments, drop_applied = self._apply_drop()
        detail = self._calculate_details(assignments)
        detail["drop_applied"] = drop_applied

        return detail


class CurvedAssignmentGroup(AssignmentGroup):
    """
    Each assignment in this group is curved and weighted equally. Assignents 
    with the lowest z-scores can be dropped due to policy. Even though
    rare, it is possible to apply clobber onto assignments.
    """
    
    def __init__(
        self, 
        weight: float, 
        corr: float = 0.6, 
        name: str = None, 
        num_drops: int = 0
    ) -> None:

        super().__init__(weight, name, num_drops)
        self.corr = corr


    def add_assignment(self, score: float, name: str=None,
                       upper: float=100, mu: float=None, sigma: float=None) -> None:

        if name == None: name = "Assignment " + str(len(self.assignments) + 1)

        new_assignment = Assignment(score, name=name, 
                                    upper=upper, mu=mu, sigma=sigma, 
                                    curved=True)
        id = new_assignment.get_id()
        self.assignments[id] = new_assignment


    def _calculate_details(self, assignments: Iterable[Assignment]) -> dict:
        """
        Calculate averaged score, mu and sigma. Then
        calculate zscore.
        """
        final_mu, final_sigma, final_score = 0, 0, 0
        n = len(assignments)

        for assignment in assignments:
            detail = assignment.get_detail()
            final_mu += detail["stats"]["mu"] / n
            final_score += detail["score"] / n
            final_sigma = correlated_sigma_sum(
                final_sigma,
                detail["stats"]["sigma"] / n,
                self.corr
            )

        final_zscore = (final_score - final_mu) / final_sigma

        detail = dict()
        detail["score"] = final_score
        detail["stats"] = {
            "zscore" : final_zscore,
            "mu" : final_mu,
            "sigma" : final_sigma
        }

        return detail


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
        num_drops: int = 0
    ) -> None:
                 
        super().__init__(weight, name, num_drops) 


    def add_assignment(self, score: float, name: str = None,
                       upper: float = 100) -> None:

        if name == None: name = "Assignment " + str(len(self.assignments) + 1)

        new_assignment = Assignment(score, name=name, upper=upper, curved=False)
        id = new_assignment.get_id()
        self.assignments[id] = new_assignment
        

    def _calculate_details(self, assignments: Iterable[Assignment]) -> dict:
        """Calculate averaged score"""
        final_score = 0
        n = len(assignments)

        for assignment in assignments:
            final_score += assignment.get_score()

        final_score = final_score / n

        detail = dict()
        detail["score"] = final_score
        detail["stats"] = dict()

        return detail


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

    Component = Union[
        CurvedAssignmentGroup, 
        UncurvedAssignmentGroup,
        CurvedSingleAssignment,
        UncurvedSingleAssignment
    ]

    def __init__(self, corr: float = 0.6, name: str = None) -> None:

        if corr < 0 or corr > 1.0: raise ValueError(f"Invalid correlation coefficient: {corr}.")

        self.corr = corr
        self.name = name if name else "My Course"
        self.components = dict()
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
            "F" : 0
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
            "F" : 0
        }


    def get_components(self) -> dict[int, Component]:
        return self.components


    def _calculate_curved_detail(
        self, 
        assignments: Iterable[Component]
    ) -> dict[str, float]:
        """
        Calculate weighted score, mu, sigma and zscore 
        for curved components
        """
        curved = {
            "score": 0,
            "mu": 0,
            "sigma": 0,
            "zscore": 0
            }

        if len(assignments) == 0: return detail
        for component in assignments:
            detail = component.get_detail()
            curved["score"] += detail["score"] * component.get_weight()
            curved["mu"] += detail["stats"]["mu"] * component.get_weight()
            curved["sigma"] = correlated_sigma_sum(
                curved["sigma"],
                detail["stats"]["sigma"] * component.get_weight(),
                self.corr
            )
        curved["zscore"] = (curved["score"] - curved["mu"]) / curved["sigma"]

        return curved


    def _calculate_uncurved_detail(
        self,
        assignments: Iterable[Component]
    ) -> float:
        """Calculate weighted score for uncurved components"""
        uncurved_score = 0
        for component in assignments:
            detail = component.get_detail()
            uncurved_score += detail["score"] * component.get_weight()
        return uncurved_score


    def _calculate_detail(
        self,
        curved: Iterable[Component],
        uncurved: Iterable[Component],
        total: float
    ) -> dict:
        """
        Calculte weighted scores, mu, sigma and zscore for
        all assignments
        """
        # Combine everthing
        curved_info = self._calculate_curved_detail(curved)
        uncurved_score = self._calculate_uncurved_detail(uncurved)

        overall_score = curved_info["score"] + uncurved_score
        final_score = overall_score / total

        overall_mu = curved_info["mu"] + uncurved_score
        final_mu = overall_mu / total

        final_sigma = curved_info["sigma"] / total
        
        detail = dict()
        detail["score"] = final_score
        detail["stats"] = {
            "zscore" : curved_info["zscore"],
            "mu" : final_mu,
            "sigma" : final_sigma
        }

        return detail


    def get_detail(self) -> dict:
        """
        Overall statistics of the course
        """
        # Iterate over components:
        # Classify into curved and uncurved.
        # Compute the total weight.
        total, curved, uncurved = 0, [], []
        for component in self.components.values():
            if component["curved"]: 
                curved.append(component["object"])
            else: uncurved.append(component["object"])
            total += component["weight"]
            if total > 1.0: raise ValueError("Total weight exceeds one.")
        
        # Check if the weights are incomplete
        is_final = isclose(total, 1.0)

        detail = self._calculate_detail(curved, uncurved, total)        
        detail["curved"] = bool(len(curved))
        detail["is_final"] = is_final

        return detail


    def get_grade(self, show_boundary=False) -> str:
        """Calclate the letter grade for ths course"""
        # Calculate letter grade using scipy.stat.truncnorm
        detail = self.get_detail()

        if detail["curved"]:
            a = (0 - detail["stats"]["mu"]) / detail["stats"]["sigma"]
            b = (1 - detail["stats"]["mu"]) / detail["stats"]["sigma"]
            X = truncnorm(a, b, loc=detail["stats"]["mu"], scale=detail["stats"]["sigma"])
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
            if detail["score"] >= v:
                break
        
        return letter_grade


    def add_curved_single(self, weight: float, score: float, name: str = None,
                          upper: float = 100, mu: float = None, sigma: float = None
                          ) -> CurvedSingleAssignment:

        if name == None: name = "Assignment " + str(len(self.components) + 1)
        new_component = CurvedSingleAssignment(
            weight, score, name, upper, mu, sigma
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
                            upper: float = 100) -> UncurvedSingleAssignment:
        if name == None: name = "Assignment " + str(len(self.components) + 1)
        new_component = UncurvedSingleAssignment(
            weight, score, name, upper
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


    def add_curved_group(self, weight: float, corr: float = None, 
                         name: str = None, num_drops: int = 0) -> CurvedAssignmentGroup:
        
        if corr == None: corr = self.corr
        if name == None: name = "Grouped Assignments " + str(len(self.components) + 1)
        new_component = CurvedAssignmentGroup(weight, corr, name, num_drops)
        id = new_component.get_id()

        info = {
            "curved": True,
            "weight": weight,
            "grouped": True,
            "object": new_component
        }

        self.components[id] = info
        return new_component


    def add_uncurved_group(self, weight: float, name: str = None, 
                           num_drops: int = 0) -> UncurvedAssignmentGroup:
        
        if name == None: name = "Grouped Assignments " + str(len(self.components) + 1)
        new_component = UncurvedAssignmentGroup(weight, name, num_drops)
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
        self, source: int, 
        targets: list[int], 
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
        clobbered_assignments = []    
        
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
            clobbered_assignments.append(min_assignment.get_id())

            capacity -= 1
        
        self.clobber_info = {
            "source": source.get_id(),
            "targets": clobbered_assignments
        }


    def revert_clobber(self):
        if self.clobber_info is None:
            raise AssertionError("Cannot revert if no clobber was applied.")
        
        for assignment in self.clobber_info["targets"]:
            assignment = self.components[assignment]["object"]
            assignment.revert_clobber()

        self.clobber_info = None