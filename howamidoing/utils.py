def correlated_sigma_sum(sigma1, sigma2, corr):
    first_term = sigma1 ** 2 + sigma2 ** 2
    second_term = 2 * corr * sigma1 * sigma2
    return (first_term + second_term) ** 0.5