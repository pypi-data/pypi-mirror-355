import math
import numpy as np


LEGENDRES_CONSTANT = 1.08366


def estimate_num_primes_below(n) -> int:
    """
    Using prime number theorem, estimate the number of primes below n

    Args:
        n (int): The maximum number to check
    Returns:
        int: The estimated number of primes below n
    """
    if n < 2:
        return 0

    return int(n / (math.log(n) - LEGENDRES_CONSTANT))


def is_prime(n) -> bool:
    """
    Returns whether or not n is prime, iusing trial division

    Args:
        n (int): The number to check
    Returns:
        bool: Whether or not n is prime
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def primes(n) -> list:
    """
    Returns a list of primes that are less than n using the Sieve of Eratosthenes

    Args:
        n (int): The maximum number to check
    Returns:
        list: The list of primes
    """
    sieve = np.ones(n, dtype=bool)
    sieve[0:2] = False

    for i in range(2, int(math.sqrt(n)) + 1):
        if sieve[i]:
            sieve[i * i::i] = False

    return np.nonzero(sieve)[0].tolist()


def segmented_sieve(n) -> list:
    """
    Returns a list of primes that are less than n using the segmented Sieve algorithm

    Args:
        n (int): The maximum number to check
    Returns:
        list: The list of primes
    """
    output = []

    limit = math.floor(math.sqrt(n)) + 1
    primes_root = primes(limit)

    low = limit
    high = limit * 2

    while low < n:
        if high >= n:
            high = n

        mark = np.ones(high - low, dtype=bool)

        for prime in primes_root:
            low_limit = max(prime, (low + prime - 1) // prime) * prime
            mark[low_limit - low:high - low:prime] = False

        output.extend(np.nonzero(mark)[0] + low)

        low += limit
        high += limit

    return primes_root + output


def get_prime_factors(x, primes_=None) -> dict:
    """
    Get the prime factors of x

    Args:
        x (int): Number to get prime factors of
    Kwargs:
        primes (list): List of primes to use for factorization
            (if not provided or the last entry is less than root of x they will be calculated)
    Returns:
        dict: Dictionary of prime factors of x
    """
    prime_factors = {}

    if primes_ is None or primes_[-1] < math.sqrt(x):
        primes_ = primes(math.ceil(math.sqrt(x)))

    for prime in primes_:
        while x % prime == 0:
            prime_factors[prime] = prime_factors.get(prime, 0) + 1
            x //= prime

    if x > 1:
        prime_factors[x] = 1

    return prime_factors
