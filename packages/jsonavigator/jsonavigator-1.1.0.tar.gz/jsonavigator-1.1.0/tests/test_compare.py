import json
import os
import pytest
from jsoninja.compare import compare_files

@pytest.fixture
def create_temp_json_files():
    """Fixture to create temporary JSON files for testing."""
    json1 = {
        "name": "Alice",
        "age": 30,
        "city": "New York"
    }
    json2 = {
        "name": "Alice",
        "age": 31,
        "city": "New York",
        "country": "USA"
    }
    json3 = {
        "name": "Alice",
        "age": 30,
        "city": "Los Angeles"
    }

    # Create temporary JSON files
    with open('test1.json', 'w', encoding='utf-8') as f:
        json.dump(json1, f)
    with open('test2.json', 'w', encoding='utf-8') as f:
        json.dump(json2, f)
    with open('test3.json', 'w', encoding='utf-8') as f:
        json.dump(json3, f)

    yield  # This allows the test to run

    # Clean up the test files
    os.remove('test1.json')
    os.remove('test2.json')
    os.remove('test3.json')

def test_compare_files_identical(create_temp_json_files):
    """Test comparing two identical JSON files."""
    result = compare_files('test1.json', 'test1.json', isPath=True)
    assert isinstance(result, tuple) and len(result) == 2  # Ensure two values are returned
    output, summary = result
    assert isinstance(output, list)  # Ensure output is a list
    assert isinstance(summary, dict)  # Ensure summary is a dictionary
    assert summary == {"message": "No differences found. The JSON files are identical."}

def test_compare_files_differences(create_temp_json_files):
    """Test comparing two different JSON files."""
    result = compare_files('test1.json', 'test2.json', isPath=True)
    assert isinstance(result, tuple) and len(result) == 2  # Ensure two values are returned
    output, summary = result
    assert isinstance(output, list)  # Ensure output is a list
    assert isinstance(summary, dict)  # Ensure summary is a dictionary
    assert summary['added'] == 1
    assert summary['removed'] == 0
    assert summary['changed'] == 1
    assert summary['type_changed'] == 0

def test_compare_files_removed_key(create_temp_json_files):
    """Test comparing JSON files with a removed key."""
    result = compare_files('test1.json', 'test3.json', isPath=True)
    assert isinstance(result, tuple) and len(result) == 2  # Ensure two values are returned
    output, summary = result
    assert isinstance(output, list)  # Ensure output is a list
    assert isinstance(summary, dict)  # Ensure summary is a dictionary
    assert summary['added'] == 0
    assert summary['removed'] == 0
    assert summary['changed'] == 1
    assert summary['type_changed'] == 0
