from time import time

def correlated_sigma_sum(sigma1: float, sigma2: float, corr: float) -> float:
    """
    Compute the standard deviation of the sum of two normally
    distributed random variables with correlation coefficient
    `corr`.
    """
    first_term = sigma1 ** 2 + sigma2 ** 2
    second_term = 2 * corr * sigma1 * sigma2
    return (first_term + second_term) ** 0.5


def generate_id(object) -> int:
    """Generate an uniqe id for an object"""
    # Code motivated by chatGPT, 2022
    # chat.openai.com
    int(time() * 1000000 + id(object))