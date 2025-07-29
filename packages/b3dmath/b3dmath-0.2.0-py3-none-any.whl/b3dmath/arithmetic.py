import b3dmath.primes
import sys


if sys.version_info.minor >= 5:
    from math import gcd
    from math import lcm
else:
    def gcd(a, b):
        """
        Given two numbers, this will return the Greatest Common Divisor.
        (The largest number that divides both evenly)

        Args:
            a (int): The first number
            b (int): The second number
        Returns:
            int: The greatest common divisor
        """
        while (b):
            a, b = b, a % b
        return a

    def lcm(a, b):
        """
        Given two numbers, this will return the Least Common Multiple.
        (The smallest number that both numbers divide evenly)

        Args:
            a (int): The first number
            b (int): The second number
        Returns:
            int: The least common multiple
        """
        return a * (b / gcd(a, b))


def num_divisors(x, primes=None):
    """
    Get the number of divisors of x

    Args:
        x (int): Number to get divisors of
    Kwargs:
        primes (list): List of cached primes to use for factorization
            (if not provided or the last entry is less than root of x they will be calculated)
    Returns:
        int: Number of divisors of x
    """
    prime_factors = b3dmath.primes.get_prime_factors(x, primes)

    output = 1
    for count in prime_factors.values():
        output *= count + 1

    return output


def divisors(x, prime_factors=None):
    """
    Get the divisors of x

    Args:
        x (int): Number to get divisors of
    Kwargs:
        prime_factors (list): List of prime factors of x
            (if not provided or the last entry is less than root of x they will be calculated)
    Returns:
        list: List of divisors of x
    """
    if x < 2:
        return [x]

    if prime_factors is None or prime_factors[-1] < x ** 0.5:
        prime_factors = b3dmath.primes.get_prime_factors(x)

    # all possible valid combinations of prime factors
    divisors = [1]
    for prime, count in prime_factors.items():
        divisors.extend(
            [d * prime ** exp for exp in range(1, count + 1) for d in divisors])

    return sorted(set(divisors))


def sum_of_divisors(n):
    """
    Calculate the sum of all divisors of a number n.

    Args:
        n (int): The number to calculate the sum of divisors for.
    Returns:
        int: The sum of all divisors of n.
    """
    i = 2
    divisors = 1
    while i * i <= n:
        if n % i:
            i += 1
        else:
            count = 0
            while n % i == 0:
                n //= i
                count += 1
            divisors *= (i ** (count + 1) - 1) // (i - 1)
    if n > 1:
        divisors *= (n ** 2 - 1) // (n - 1)
    return divisors
