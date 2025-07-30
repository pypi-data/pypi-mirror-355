import random
from sympy import isprime, primitive_root

def generate_prime(bits: int = 256) -> int:
    """Генерация простого числа заданной длины"""
    while True:
        p = random.getrandbits(bits)
        if isprime(p):
            return p

def find_generator(p: int) -> int:
    """Поиск генератора для простого числа"""
    if not isprime(p):
        raise ValueError("Число должно быть простым")
    return primitive_root(p)