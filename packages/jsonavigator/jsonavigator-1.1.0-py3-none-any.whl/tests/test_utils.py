import pytest
from jsoninja.exceptions import InvalidPathError
from jsoninja.utils import (
    validate_path,
    format_path,
    flatten_json,
)

# Test cases for validate_path
def test_validate_path_valid():
    """
    Test validating a properly formatted path.
    """
    assert validate_path("a.b[1]") == True

def test_validate_path_invalid_type():
    """
    Test validating an invalid path type (not a string).
    """
    with pytest.raises(InvalidPathError, match="Path must be a string."):
        validate_path(123)  # Path is not a string

def test_validate_path_invalid_characters():
    """
    Test validating a path with invalid characters.
    """
    with pytest.raises(InvalidPathError, match="Invalid character '#' in path."):
        validate_path("a.b#[1]")  # Invalid character

def test_validate_path_mismatched_brackets():
    """
    Test validating a path with mismatched brackets.
    """
    with pytest.raises(InvalidPathError, match="Mismatched brackets in path."):
        validate_path("a.b[1")  # Mismatched brackets

# Test cases for format_path
def test_format_path():
    """
    Test formatting a path for better readability.
    """
    assert format_path("a.b[1]") == "a -> b[1]"


def test_format_path_invalid_type():
    """
    Test formatting an invalid path type (not a string).
    """
    with pytest.raises(InvalidPathError, match="Path must be a string."):
        format_path(123)  # Path is not a string


# Test cases for flatten_json
def test_flatten_json():
    """
    Test flattening a simple nested JSON structure.
    """
    data = {"a": {"b": [1, 2], "c": 3}}
    expected = {
        "a.b[0]": 1,
        "a.b[1]": 2,
        "a.c": 3
    }
    assert flatten_json(data) == expected


def test_flatten_json_empty():
    """
    Test flattening an empty dictionary.
    """
    data = {}
    expected = {}
    assert flatten_json(data) == expected


def test_flatten_json_nested_lists():
    """
    Test flattening a JSON structure with nested lists.
    """
    data = {"a": [{"b": 1}, {"c": 2}]}
    expected = {
        "a[0].b": 1,
        "a[1].c": 2
    }
    assert flatten_json(data) == expected
