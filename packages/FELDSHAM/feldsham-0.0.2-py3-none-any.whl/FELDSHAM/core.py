import random
import hashlib
from typing import List, Tuple

class FeldmanShamirSecretSharing:
    def __init__(self, p: int, g: int):
        """        
        Инициализация схемы Фельдмана-Шамира
        :param p: большое простое число
        :param g: генератор группы
        """
        self.p = p
        self.g = g
    
    def generate_shares(self, secret: int, n: int, t: int) -> Tuple[List[Tuple[int, int]], List[int]]:
        """
        Генерация долей секрета
        :param secret: секретное число
        :param n: общее количество долей
        :param t: пороговое количество для восстановления
        :return: (доли, коэффициенты полинома)
        """
        if t > n:
            raise ValueError("Порог t не может быть больше общего количества долей n")
        
        # Генерация случайных коэффициентов полинома
        coefficients = [secret] + [random.randint(1, self.p-1) for _ in range(t-1)]
        
        shares = []
        for i in range(1, n+1):
            # Вычисление значения полинома в точке i
            share = 0
            for j, coeff in enumerate(coefficients):
                share += coeff * (i ** j)
            share %= self.p
            shares.append((i, share))
        
        return shares, coefficients
    
    def verify_share(self, share: Tuple[int, int], commitments: List[int]) -> bool:
        """
        Проверка корректности доли с использованием обязательств Фельдмана
        :param share: доля (x, y)
        :param commitments: обязательства (g^a0, g^a1, ..., g^at-1)
        :return: True если доля корректна, иначе False
        """
        x, y = share
        lhs = pow(self.g, y, self.p)
        
        rhs = 1
        for j, comm in enumerate(commitments):
            rhs *= pow(comm, x ** j, self.p)
            rhs %= self.p
        
        return lhs == rhs
    
    def reconstruct_secret(self, shares: List[Tuple[int, int]]) -> int:
        """
        Восстановление секрета с использованием интерполяции Лагранжа
        :param shares: список долей (x, y)
        :return: восстановленный секрет
        """
        secret = 0
        for i, (xi, yi) in enumerate(shares):
            numerator, denominator = 1, 1
            for j, (xj, _) in enumerate(shares):
                if i != j:
                    numerator *= (-xj)
                    denominator *= (xi - xj)
            lagrange_coeff = numerator * pow(denominator, -1, self.p) % self.p
            secret = (secret + yi * lagrange_coeff) % self.p
        return secret
    
    def generate_commitments(self, coefficients: List[int]) -> List[int]:
        """
        Генерация обязательств Фельдмана
        :param coefficients: коэффициенты полинома
        :return: список обязательств (g^a0, g^a1, ..., g^at-1)
        """
        return [pow(self.g, coeff, self.p) for coeff in coefficients]#Code goes here