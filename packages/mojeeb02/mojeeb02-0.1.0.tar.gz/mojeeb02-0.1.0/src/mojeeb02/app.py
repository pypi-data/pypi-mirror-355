def is_even(number):
    return number % 2 == 0

def is_odd(number):
    return number % 2 != 0

def is_prime(number):
    if number <= 1:
        return False
    for i in range(2, number):
        if number % i == 0:
            return False