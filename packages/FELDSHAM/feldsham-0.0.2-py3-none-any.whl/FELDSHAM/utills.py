import random
from sympy import isprime, primitive_root

def generate_prime(bits: int = 256) -> int:
    """Генерация большого простого числа"""
    while True:
        p = random.getrandbits(bits)
        if isprime(p):
            return p

def find_generator(p: int) -> int:
    """Нахождение генератора для простого числа"""
    return primitive_root(p)#Code goes here