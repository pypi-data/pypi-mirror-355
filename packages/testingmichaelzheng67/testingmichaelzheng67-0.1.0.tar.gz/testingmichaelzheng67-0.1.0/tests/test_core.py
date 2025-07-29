# tests/test_core.py
from src import greet

def test_greet():
    assert greet("Alice") == "Hello, Alice!"
