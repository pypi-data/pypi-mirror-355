class SecretReconstructor:
    def __init__(self, p: int):
        """
        Инициализация реконструктора
        :param p: простое число (модуль)
        """
        self.p = p
    
    def reconstruct_secret(self, shares: List[Tuple[int, int]]) -> int:
        """
        Восстановление секрета по долям
        :param shares: список долей [(x1, y1), (x2, y2), ...]
        :return: восстановленный секрет
        """
        if not shares:
            raise ValueError("Необходимы доли для восстановления")
            
        secret = 0
        for i, (xi, yi) in enumerate(shares):
            numerator, denominator = 1, 1
            
            for j, (xj, _) in enumerate(shares):
                if i != j:
                    numerator *= (-xj)
                    denominator *= (xi - xj)
                    
            lagrange_coeff = (numerator * pow(denominator, -1, self.p)) % self.p
            secret = (secret + yi * lagrange_coeff) % self.p
            
        return secret