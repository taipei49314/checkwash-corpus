from app.gcd import gcd
import math

def calculate_gcd(a, b):
    return math.gcd(a, b)

def test_gcd():
    assert calculate_gcd(12, 8) == 4
