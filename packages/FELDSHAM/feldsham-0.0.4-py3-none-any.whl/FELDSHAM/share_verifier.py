class ShareVerifier:
    def __init__(self, p: int, g: int):
        """
        Инициализация верификатора
        :param p: простое число (должно совпадать с генератором)
        :param g: генератор группы
        """
        self.p = p
        self.g = g
    
    def verify_share(self, share: Tuple[int, int], commitments: List[int]) -> bool:
        """
        Проверка корректности доли
        :param share: кортеж (id, значение доли)
        :param commitments: список обязательств
        :return: True если доля корректна
        """
        x, y = share
        if not commitments:
            raise ValueError("Необходимы обязательства для проверки")
            
        # Вычисление g^y mod p
        lhs = pow(self.g, y, self.p)
        
        # Вычисление произведения commitments[j]^(x^j) mod p
        rhs = 1
        for j, comm in enumerate(commitments):
            rhs = (rhs * pow(comm, x ** j, self.p)) % self.p
            
        return lhs == rhs