from math import isclose
from scipy.stats import truncnorm
from .utils import *

class Assignment:
    """
    A generic assignment. The primary definition of an assignment
    is the score. If the assignment is graded on a curved basis, then
    it also must be defined by the mean (`mu`) and standard deviation
    (`sigma`). Additionally, the score could be replaced by a zscore
    if the assignment is curved--in this case, this assignment is 
    clobbered. This class is inaccessible from user.

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
    zscore : :obj:`bool`, optional
        Whether the score entered for this assignment is a zscore. Set
        to true is this assignment is being clobbered. Defaults to False.
    """

    def __init__(self, score: float, name: str=None,
                 upper: float=100, mu: float=None, sigma: float=None,
                 curved: bool=None, zscore=False) -> None:
        self.name = name
        self.upper = upper
        
        if zscore and not curved:
            raise ValueError("Can't take zscore if not curved.")
        
        if curved and (mu == None or sigma == None):
            raise ValueError("Curved assignment must have mean and standard deviation.")

        self.curved = curved
        self.mu = mu / self.upper if mu else None
        self.sigma = sigma / self.upper if sigma else None

        # Clobbered (z-score is provided).
        # Calculate actual raw score.
        if zscore:
            self.zscore = score
            self.score = (self.zscore * self.sigma) + self.mu
        # Curved assignment.
        # Calculate z-score.
        elif curved:
            self.score = score / self.upper
            self.zscore = (self.score - self.mu) / self.sigma
        # Un-curved assignment
        # No zscore
        else:
            self.zscore = 0
            self.score = score / self.upper


    def get_score(self) -> float:
        """Return score"""
        return self.score

    
    def get_zscore(self) -> float:
        """Return zscore"""
        return self.zscore

        
    def get_detail(self) -> dict:
        """
        Return a dictionary of full details about this
        assignment. Includes score and potentially the
        mean, standard deviation, and zscore of this 
        assignment if curved.
        """
        detail = dict()
        detail["score"] = self.score
        
        if not self.curved:
            detail["stats"] = dict()
        else:
            detail["stats"] = {
                "zscore" : self.zscore,
                "mu" : self.mu,
                "sigma" : self.sigma
            }

        return detail

    
    def apply_clobber(self, score) -> None:
        self.zscore = score
        self.score = (self.zscore * self.sigma) + self.mu


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
    zscore : :obj:`bool`, optional
        Whether the score entered for this assignment is a zscore. Set
        to true is this assignment is being clobbered. Defaults to False.
    """

    def __init__(self, weight: float, score: float, name: str = None, 
                 upper: float = 100, mu: float = None, sigma: float = None, 
                 zscore=False) -> None:

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        super().__init__(score, name, upper, mu, sigma, curved=True, zscore=zscore)
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

    def __init__(self, weight: float, score: float, name: str = None, 
                 upper: float = 100) -> None:

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        super().__init__(score, name, upper, curved=False)
        self.weight = weight


class AssignmentGroup:
    
    def __init__(self, weight: float, name: str = None, num_drops: int = 0) -> None:

        if weight > 1.0 or weight <= 0: raise ValueError(f"Invalid weight: {weight}.")

        self.assignments = list()
        self.weight = weight
        self.name = name
        self.num_drops = num_drops

    
    def add_assignment(self) -> None:
        return NotImplementedError


    def get_detail(self) -> dict():
        return NotImplementedError

    
    def get_assignments(self) -> list:
        return self.assignments


    def get_num_drops(self) -> int:
        return self.num_drops


class CurvedAssignmentGroup(AssignmentGroup):
    """
    Each assignment in this group is curved and weighted equally. Assignents 
    with the lowest z-scores can be dropped due to policy. Even though
    rare, it is possible to apply clobber onto assignments.
    """
    
    def __init__(self, weight: float, corr: float = 0.6, 
                 name: str = None, num_drops: int = 0) -> None:

        super().__init__(weight, name, num_drops)
        self.corr = corr


    def calculate_details(self, assignments:set) -> float:
            
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


    def add_assignment(self, score: float, name: str=None,
                       upper: float=100, mu: float=None, sigma: float=None,
                       zscore=False) -> None:
        if name == None:
            name = "Assignment " + str(len(self.assignments) + 1)

        new_assignment = Assignment(score, name=name, 
                                    upper=upper, mu=mu, sigma=sigma, 
                                    curved=True, zscore=zscore)
        self.assignments.append(new_assignment)


    def get_detail(self) -> dict():
        assignments = self.assignments.copy()
        # sort assignments according to z-score
        assignments.sort(key= lambda i: i.get_zscore())
        # drop lowest num_drops assignments
        if len(assignments) > self.num_drops:
            assignments = assignments[self.num_drops:]
            drop_applied = True
        else:
            drop_applied = False

        detail = self.calculate_details(assignments)
        detail["drop_applied"] = drop_applied

        return detail


class UncurvedAssignmentGroup(AssignmentGroup):
    """
    Each assignment in this group is curved and weighted equally. Assignents 
    with the lowest z-scores can be dropped due to policy. Even though
    rare, it is possible to apply clobber onto assignments.
    """
    
    def __init__(self, weight: float, 
                 name: str = None, num_drops: int = 0) -> None:
                 
        super().__init__(weight, name, num_drops)
        

    def calculate_details(self, assignments:set) -> float:
        final_score = 0
        n = len(assignments)

        for assignment in assignments:
            final_score += assignment.get_score()

        final_score = final_score / n

        detail = dict()
        detail["score"] = final_score
        detail["stats"] = dict()

        return detail


    def add_assignment(self, score: float, name: str=None,
                       upper: float=100) -> None:
        if name == None:
            name = "Assignment " + str(len(self.assignments) + 1)

        new_assignment = Assignment(score, name=name, upper=upper, curved=False)
        self.assignments.append(new_assignment)
        

    def get_detail(self) -> dict():
        assignments = self.assignments.copy()
        # sort assignments according to score
        assignments.sort(key= lambda i: i.get_score())
        # drop lowest num_drops assignments
        if len(assignments) > self.num_drops:
            assignments = assignments[self.num_drops:]
            drop_applied = True
        else:
            drop_applied = False
        
        detail = self.calculate_details(assignments)
        detail["drop_applied"] = drop_applied

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

    def __init__(self, corr: float = 0.6, name: str = None) -> None:

        if corr < 0 or corr > 1.0: raise ValueError(f"Invalid correlation coefficient: {corr}.")

        self.corr = corr
        self.name = name if name else "My Course"
        self.components = dict()

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


    def get_components(self) -> list:
        return self.components


    def get_detail(self, show_boundary=False) -> dict:
        """
        Overall statistics of the course
        """
        total, curved, uncurved = 0, [], []
        contain_curved = False
        # Iterate over components:
        # Classify into curved and uncurved.
        # Compute the total weight.
        for component in self.components.values():
            if component["curved"]: 
                curved.append(component["object"])
                contain_curved = True
            else: uncurved.append(component["object"])
            total += component["weight"]
            if total > 1.0: raise ValueError("Total weight exceeds one.")
        
        # Check if the weights are incomplete
        is_final = isclose(total, 1.0)
        
        # First compute overall z-score for curved assignments
        curved_mu, curved_sigma, curved_score = 0, 0, 0
        for component in curved:
            detail = component.get_detail()
            curved_mu += detail["stats"]["mu"] * component.weight
            curved_score += detail["score"] * component.weight
            curved_sigma = correlated_sigma_sum(
                curved_sigma,
                detail["stats"]["sigma"] * component.weight,
                self.corr
            )

        # Compute z-score only if curved assignments exist
        final_zscore = 0
        if contain_curved:
            final_zscore = (curved_score - curved_mu) / curved_sigma

        # Then compute the uncurved score
        uncurved_score = 0
        for component in uncurved:
            detail = component.get_detail()
            uncurved_score += detail["score"] * component.weight

        # Combine everthing
        overall_score = curved_score + uncurved_score
        final_score = overall_score / total

        overall_mu = curved_mu + uncurved_score
        final_mu = overall_mu / total

        final_sigma = curved_sigma / total
        
        detail = dict()
        detail["score"] = final_score
        detail["stats"] = {
            "zscore" : final_zscore,
            "mu" : final_mu,
            "sigma" : final_sigma
        }
        detail["curved"] = contain_curved
        detail["is_final"] = is_final

        # Calculate letter grade using scipy.stat.truncnorm
        if contain_curved:
            a, b = (0 - final_mu) / final_sigma, (1 - final_mu) / final_sigma
            X = truncnorm(a, b, loc=final_mu, scale=final_sigma)
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
            if final_score >= v:
                break
        detail["letter_grade"] = letter_grade
        
        return detail


    def add_curved_single(self, weight: float, score: float, name: str = None,
                          upper: float = 100, mu: float = None, sigma: float = None,
                          zscore=False) -> CurvedSingleAssignment:

        if name == None: name = "Assignment " + str(len(self.components) + 1)
        new_component = CurvedSingleAssignment(
            weight, score, name, upper, mu, sigma, zscore
        )

        info = {
            "curved": True,
            "weight": weight,
            "grouped": False,
            "object": new_component
        }

        self.components[new_component] = info
        return new_component
    

    def add_uncurved_single(self, weight: float, score: float, name: str = None, 
                            upper: float = 100) -> UncurvedSingleAssignment:
        if name == None: name = "Assignment " + str(len(self.components) + 1)
        new_component = UncurvedSingleAssignment(
            weight, score, name, upper
        )

        info = {
            "curved": False,
            "weight": weight,
            "grouped": False,
            "object": new_component
        }

        self.components[new_component] = info
        return new_component


    def add_curved_group(self, weight: float, corr: float = None, 
                         name: str = None, num_drops: int = 0) -> CurvedAssignmentGroup:
        
        if corr == None: corr = self.corr
        if name == None: name = "Grouped Assignments " + str(len(self.components) + 1)
        new_component = CurvedAssignmentGroup(weight, corr, name, num_drops)

        info = {
            "curved": True,
            "weight": weight,
            "grouped": True,
            "object": new_component
        }

        self.components[new_component] = info
        return new_component


    def add_uncurved_group(self, weight: float, name: str = None, num_drops: int = 0) -> UncurvedAssignmentGroup:
        
        if name == None: name = "Grouped Assignments " + str(len(self.components) + 1)
        new_component = UncurvedAssignmentGroup(weight, name, num_drops)

        info = {
            "curved": False,
            "weight": weight,
            "grouped": True,
            "object": new_component
        }

        self.components[new_component] = info
        return new_component

    
    def apply_clobber(self, source, targets, capacity=-1) -> list:
        
        def argmin(iterable):
            return min(enumerate(iterable), key=lambda x: x[1])[0]

        if capacity == -1: capacity = len(targets)

        # Check for errors: 
        # (1) source in targets
        # (2) assignemnt not in self.components
        # (3) Assignment not curved
        # (4) Assignment is grouped
        if source in targets: raise ValueError("Source assignment cannot be in targets.")

        if source not in self.components.keys(): raise ValueError("Source assignment not found.")
        elif not self.components[source]["curved"]: raise ValueError("Source assignment is not curved.")
        elif self.components[source]["grouped"]: raise ValueError("Source assignment must be single not grouped.")

        for i, target in enumerate(targets):
            if target not in self.components.keys(): raise ValueError(f"Target assignment at index {i} not found")
            elif not self.components[target]["curved"]: raise ValueError(f"Target assignment at index {i} is not curved.")
            elif self.components[target]["grouped"]: raise ValueError(f"Target assignment at index {i} must be single not grouped.")
        print("Error check passed.")

        # Fetch the zscores for clobbering
        z_source = source.get_zscore()
        z_targets = [i.get_zscore() for i in targets]
        clobbered_assignments = []    
        
        # Apply clobber while we have capacity
        while capacity != 0:
            print("DEBUG", z_source, z_targets)
            # Zscore from source is no longer larger than any zscore from targets
            # Stop applying clobber
            if all([z_source <= z for z in z_targets]): break

            # Find the index of the assignment with minimum zscore.
            # Pop that assignment from the targets list and apply clobber
            min_index = argmin(z_targets)
            min_assignment = targets.pop(min_index)
            del z_targets[min_index]

            min_assignment.apply_clobber(z_source)
            clobbered_assignments.append(min_assignment)

            capacity -= 1

        return clobbered_assignments



