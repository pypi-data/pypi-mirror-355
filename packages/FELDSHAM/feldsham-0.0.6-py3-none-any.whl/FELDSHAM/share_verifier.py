class ShareVerifier:
    def __init__(self, p: int, g: int):
        self.p = p
        self.g = g
    
    def verify_share(self, share: tuple, commitments: list) -> bool:
        x, y = share
        lhs = pow(self.g, y, self.p)
        rhs = 1
        for j, comm in enumerate(commitments):
            rhs = (rhs * pow(comm, x ** j, self.p)) % self.p
        return lhs == rhs