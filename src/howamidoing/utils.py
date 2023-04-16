from time import time

class ID(str):
    """Identifier for objects"""

    def __init__(self, value) -> None:
        super().__init__()
        try:
            self.value = str(value)
        except:
            raise TypeError(f"{type(value)} cannot be converted to string.")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return str(self)
    
    def __hash__(self):
        return hash(self.value)
    
    def __eq__(self, other):
        return self.value.__str__() == other.__str__()
    

class Summary():
    """
    A dictionary with fixed strcuture.
    Summaries applies to ``Assignment``s, ``AssignmentGroup``s,
    and ``Course``s.
    
    {
        "_percentage" : float fraction score (0.82343172...), [for all]
        "percentage" : string percentage score (82.34%), [for all]
        "zscore" : zscore (1.21), [for all curved]
        "_mu" : fraction mu (0.3025...), [for all curved]
        "mu" : percentage mu (30.25%), [for all curved]
        "_sigma" : fraction sigma (0.1253...) [for all curved]
        "sigma" : percentage sigma (12.53), [for all curved]
        "drop_applied" : bool, [Group]
        "is_final" : bool, [Course]
        "class_curved" : bool, [Course]
        "grade" : bool, [Course]
        "error_messahe" : error message if exist [for all]
    }
    """

    def __init__(
            self,
            score : float,
            upper : float,
            zscore : float = None,
            mu : float = None,
            sigma : float = None,
            ) -> None:
        summary = dict()
        summary["_percentage"] = score / upper
        summary["percentage"] = self.percentage(summary["_percentage"])
        summary["zscore"] = round(zscore, 2) if zscore else None
        summary["_mu"] = mu / upper if mu else None
        summary["mu"] = self.percentage(summary["_mu"]) if mu else None
        summary["_sigma"] = sigma / upper if sigma else None
        summary["sigma"] = self.percentage(summary["_sigma"]) if sigma else None
        summary["drop_applied"] = None
        summary["is_final"] = None
        summary["class_curved"] = None
        summary["grade"] = None
        summary["error_message"] = None

        self.summary = summary

    def __repr__(self) -> str:
        return self.summary.__repr__()
    
    def __str__(self) -> str:
        return self.summary.__str__()
    
    def __getitem__(self, key: str) -> str:
        return self.summary[key]

    def __setitem__(self, key: str, value) -> None:
        if key not in self.summary:
            raise ValueError("Summary cannot accept assignment on unsupported fields")
        self.summary[key] = value 

    def percentage(self, fraction : float) -> str:
        "Turn float into percentage display string"
        return str(round(fraction * 100, 2) ) + "%"

    def to_dict(self) -> dict:
        return self.summary

def correlated_sigma_sum(sigma1: float, sigma2: float, corr: float) -> float:
    """
    Compute the standard deviation of the sum of two normally
    distributed random variables with correlation coefficient
    `corr`.
    """
    first_term = sigma1 ** 2 + sigma2 ** 2
    second_term = 2 * corr * sigma1 * sigma2
    return (first_term + second_term) ** 0.5


def generate_id(object) -> ID:
    """Generate an uniqe id for an object"""
    # Code motivated by chatGPT, 2022
    # chat.openai.com
    return ID(str(int(time() * 1000000 + id(object))))