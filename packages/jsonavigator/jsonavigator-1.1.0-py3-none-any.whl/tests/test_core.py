import pytest
from jsoninja.core import *

def test_traverse_json():
    data = {"a": {"b": [1, 2], "c": 3}}
    expected = [
        ("a.b[0]", 1),
        ("a.b[1]", 2),
        ("a.c", 3)
    ]
    assert list(traverse_json(data)) == expected

def test_get_value_at_path():
    data = {"a": {"b": [1, 2], "c": 3}}
    assert get_value_at_path(data, "a.b[1]") == 2
    assert get_value_at_path(data, "a.c") == 3

# Test Case: Key Found in a Flat Dictionary
def test_find_value_in_flat_dict():
    data = {"a": 1, "b": 2, "c": 3}
    assert find_value_of_element("b", data) == 2

# Test Case: Key Not Found in a Flat Dictionary
def test_find_value_not_found_in_flat_dict():
    data = {"a": 1, "b": 2, "c": 3}
    assert find_value_of_element("d", data) == ''

# Test Case: Key Found in a Nested Dictionary
def test_find_value_in_nested_dict():
    data = {"a": {"b": {"c": 42}}}
    assert find_value_of_element("c", data) == 42

# Test Case: Key Not Found in a Nested Dictionary
def test_find_value_not_found_in_nested_dict():
    data = {"a": {"b": {"c": 42}}}
    assert find_value_of_element("d", data) == ''

# Test Case: Key Found in a List of Dictionaries
def test_find_value_in_list_of_dicts():
    data = [{"a": 1}, {"b": 2}, {"c": 3}]
    assert find_value_of_element("b", data) == 2

# Test Case: Key Not Found in a List of Dictionaries
def test_find_value_not_found_in_list_of_dicts():
    data = [{"a": 1}, {"b": 2}, {"c": 3}]
    assert find_value_of_element("d", data) == ''

# Test Case: Key Found in a Deeply Nested Structure
def test_find_value_in_deeply_nested_structure():
    data = {
        "a": {
            "b": [
                {"c": 1},
                {"d": 2},
                {"e": {"f": 42}}
            ]
        }
    }
    assert find_value_of_element("f", data) == 42

# Test Case: Key Not Found in a Deeply Nested Structure
def test_find_value_not_found_in_deeply_nested_structure():
    data = {
        "a": {
            "b": [
                {"c": 1},
                {"d": 2},
                {"e": {"f": 42}}
            ]
        }
    }
    assert find_value_of_element("g", data) == ''

# Test Case: Empty Data Structure
def test_find_value_in_empty_data():
    data = {}
    assert find_value_of_element("a", data) == ''

# Test Case: Non-Dict/Non-List Input
def test_find_value_in_non_dict_non_list():
    data = "invalid"
    assert find_value_of_element("a", data) == ''

# Test Case: Multiple Matches (Returns First Occurrence)
def test_find_value_with_multiple_matches():
    data = {"a": 1, "b": {"a": 2}, "c": [{"a": 3}, {"d": 4}]}
    assert find_value_of_element("a", data) == 1  # Returns the first occurrence

# Test Case: Exception Handling
def test_find_value_exception_handling():
    data = {"a": {"b": {"c": 42}}}
    # Simulate an exception by passing an invalid data type
    assert find_value_of_element("c", "invalid_data") == ''


# Test Case: Key Found in a Flat Dictionary
def test_find_all_paths_in_flat_dict():
    data = {"a": 1, "b": 2, "c": 3}
    result = find_all_paths_for_element(data, "b")
    assert result == ["b"]

# Test Case: Key Not Found in a Flat Dictionary
def test_find_all_paths_not_found_in_flat_dict():
    data = {"a": 1, "b": 2, "c": 3}
    result = find_all_paths_for_element(data, "d")
    assert result == []

# Test Case: Key Found in a Nested Dictionary
def test_find_all_paths_in_nested_dict():
    data = {"a": {"b": {"c": 42}}}
    result = find_all_paths_for_element(data, "c")
    assert result == ["a.b.c"]

# Test Case: Key Not Found in a Nested Dictionary
def test_find_all_paths_not_found_in_nested_dict():
    data = {"a": {"b": {"c": 42}}}
    result = find_all_paths_for_element(data, "d")
    assert result == []

# Test Case: Key Found in a List of Dictionaries
def test_find_all_paths_in_list_of_dicts():
    data = [{"a": 1}, {"b": 2}, {"c": 3}]
    result = find_all_paths_for_element(data, "b")
    assert result == ["[1].b"]

# Test Case: Key Not Found in a List of Dictionaries
def test_find_all_paths_not_found_in_list_of_dicts():
    data = [{"a": 1}, {"b": 2}, {"c": 3}]
    result = find_all_paths_for_element(data, "d")
    assert result == []

# Test Case: Key Found in a Deeply Nested Structure
def test_find_all_paths_in_deeply_nested_structure():
    data = {
        "a": {
            "b": [
                {"c": 1},
                {"d": 2},
                {"e": {"f": 42}}
            ]
        }
    }
    result = find_all_paths_for_element(data, "f")
    assert result == ["a.b[2].e.f"]

# Test Case: Key Not Found in a Deeply Nested Structure
def test_find_all_paths_not_found_in_deeply_nested_structure():
    data = {
        "a": {
            "b": [
                {"c": 1},
                {"d": 2},
                {"e": {"f": 42}}
            ]
        }
    }
    result = find_all_paths_for_element(data, "g")
    assert result == []

# Test Case: Multiple Matches (Returns All Paths)
def test_find_all_paths_with_multiple_matches():
    data = {"a": 1, "b": {"a": 2}, "c": [{"a": 3}, {"d": 4}]}
    result = find_all_paths_for_element(data, "a")
    assert result == ["a", "b.a", "c[0].a"]

# Test Case: Empty Data Structure
def test_find_all_paths_in_empty_data():
    data = {}
    result = find_all_paths_for_element(data, "a")
    assert result == []

# Test Case: Non-Dict/Non-List Input
def test_find_all_paths_in_non_dict_non_list():
    data = "invalid"
    result = find_all_paths_for_element(data, "a")
    assert result == []

# Test Case: Custom Separator
def test_find_all_paths_with_custom_separator():
    data = {"a": {"b": {"c": 42}}}
    result = find_all_paths_for_element(data, "c", separator="/")
    assert result == ["a/b/c"]

# Test Case: Exception Handling
def test_find_all_paths_exception_handling():
    data = {"a": {"b": {"c": 42}}}
    # Simulate an exception by passing an invalid data type
    result = find_all_paths_for_element("invalid_data", "c")
    assert result == []




# Test Case: Empty All Values in a Flat Dictionary
def test_empty_flat_dict():
    data = {"a": 1, "b": "hello", "c": True}
    expected = {"a": "", "b": "", "c": ""}
    assert empty_all_the_values(data) == expected

# Test Case: Empty All Values in a Nested Dictionary
def test_empty_nested_dict():
    data = {"a": {"b": 42, "c": "world"}, "d": True}
    expected = {"a": {"b": "", "c": ""}, "d": ""}
    assert empty_all_the_values(data) == expected

# Test Case: Empty All Values in a List
def test_empty_list():
    data = [1, "hello", True]
    expected = ["", "", ""]
    assert empty_all_the_values(data) == expected

# Test Case: Empty All Values in a Nested List
def test_empty_nested_list():
    data = [1, [2, {"a": 42}], [{"b": "world"}]]
    expected = ["", ["", {"a": ""}], [{"b": ""}]]
    assert empty_all_the_values(data) == expected

# Test Case: Empty All Values in a Mixed Structure
def test_empty_mixed_structure():
    data = {
        "a": 1,
        "b": {"c": 42, "d": [1, 2, {"e": "hello"}]},
        "f": [True, {"g": "world"}],
    }
    expected = {
        "a": "",
        "b": {"c": "", "d": ["", "", {"e": ""}]},
        "f": ["", {"g": ""}],
    }
    assert empty_all_the_values(data) == expected

# Test Case: Empty an Already Empty Dictionary
def test_empty_already_empty_dict():
    data = {}
    expected = {}
    assert empty_all_the_values(data) == expected

# Test Case: Empty an Already Empty List
def test_empty_already_empty_list():
    data = []
    expected = []
    assert empty_all_the_values(data) == expected

# Test Case: Handle Non-Dict/Non-List Input
def test_empty_non_dict_non_list():
    data = "invalid"
    assert empty_all_the_values(data) is None

# Test Case: Exception Handling
def test_empty_exception_handling():
    data = {"a": {"b": 42}}
    # Simulate an exception by passing an invalid input type
    result = empty_all_the_values(123)
    assert result is None