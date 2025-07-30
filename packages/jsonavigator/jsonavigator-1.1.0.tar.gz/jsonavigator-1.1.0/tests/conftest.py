# tests/conftest.py

import pytest

@pytest.fixture
def sample_json():
    return {"a": {"b": [1, 2], "c": 3}}