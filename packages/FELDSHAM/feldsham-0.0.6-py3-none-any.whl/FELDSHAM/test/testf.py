import pytest
import sys
import os

# Добавляем путь к основному пакету
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from FELDSHAM.share_generator import ShareGenerator
from FELDSHAM.share_verifier import ShareVerifier
from FELDSHAM.secret_reconstructor import SecretReconstructor
from FELDSHAM.utills import generate_prime, find_generator

class TestShareGenerator:
    def test_generate_shares(self):
        p = generate_prime(256)
        g = find_generator(p)
        gen = ShareGenerator(p, g)
        shares, coeffs = gen.generate_shares(secret=42, n=5, t=3)
        assert len(shares) == 5
        assert len(coeffs) == 3

class TestShareVerifier:
    def test_verify_share(self):
        p = generate_prime(256)
        g = find_generator(p)
        verifier = ShareVerifier(p, g)
        # Тестовые данные
        assert verifier.verify_share((1, 5), [pow(g, 2, p), pow(g, 3, p)])

if __name__ == "__main__":
    pytest.main()