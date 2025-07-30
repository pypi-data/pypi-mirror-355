import random
from typing import List, Tuple

class ShareGenerator:
    def __init__(self, p: int, g: int):
        """
        Инициализация с параметрами схемы
        :param p: простое число
        :param g: генератор группы
        """
        self.p = p
        self.g = g
    
    def generate_shares(self, secret: int, n: int, t: int) -> Tuple[List[Tuple[int, int]], List[int]]:
        """
        Генерация долей секрета
        :param secret: секретное число
        :param n: общее количество долей
        :param t: пороговое количество
        :return: (доли, коэффициенты полинома)
        """
        if not 0 < secret < self.p:
            raise ValueError("Секрет должен быть в диапазоне (0, p)")
        if t > n:
            raise ValueError("Порог t не может быть больше n")
        
        coefficients = [secret] + [random.randint(1, self.p-1) for _ in range(t-1)]
        shares = []
        
        for i in range(1, n+1):
            share = sum(coeff * (i ** j) for j, coeff in enumerate(coefficients)) % self.p
            shares.append((i, share))
            
        return shares, coefficients
    
    def generate_commitments(self, coefficients: List[int]) -> List[int]:
        """
        Генерация обязательств Фельдмана
        :param coefficients: коэффициенты полинома
        :return: список обязательств [g^a0, g^a1, ...]
        """
        return [pow(self.g, coeff, self.p) for coeff in coefficients]