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
        "percentage" : percentage score (12.34%), [for all]
        "score" : score (90.50), [for all]
        "zscore" : zscore (1.21), [for all curved]
        "mu" : mu (30.25), [for all curved]
        "sigma" : sigma (12.53), [for all curved]
        "drop_applied" : bool, [Group]
        "is_final" : bool, [Course]
        "curved" : bool, [Course]
        "grade" : bool, [Course]
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
        summary["percentage"] = str(round(score / upper, 4) * 100) + "%"
        summary["score"] = str(round(score, 2))
        summary["zscore"] = str(round(zscore, 2)) if zscore else None
        summary["mu"] = str(round(mu, 2)) if mu else None
        summary["sigma"] = str(round(sigma, 2)) if sigma else None

        self.summary = summary

    def __repr__(self) -> str:
        return self.summary.__repr__()
    
    def __str__(self) -> str:
        return self.summary.__str__()
    
    def __getitem__(self, key: str) -> str:
        return self.summary[key]



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