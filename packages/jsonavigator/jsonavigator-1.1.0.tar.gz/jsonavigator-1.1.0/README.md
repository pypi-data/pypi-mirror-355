
# JSONavigator  [![PyPI Downloads](https://static.pepy.tech/badge/jsonavigator)](https://pepy.tech/projects/jsonavigator) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Nikhil-Singh-2503/JSONavigator/publish-to-pypi.yml)


JSONavigator is a Python package designed to simplify working with nested JSON structures. It provides utilities for traversing, flattening, validating, formatting JSON paths and comparing JSONs. Streamline your JSON data processing tasks with ease and efficiency.



## **Features**
- **Traverse Nested JSON**: Recursively traverse dictionaries and lists to extract paths and values.
- **Flatten JSON**: Convert nested JSON into a single-level dictionary for easier access.
- **Validate Paths**: Ensure that JSON paths are properly formatted and valid.
- **Format Paths**: Improve readability of JSON paths by replacing separators with more user-friendly formats.
- **Find Values**: Search for specific keys in nested JSON and retrieve their associated values.
- **Empty All Values**: Replace all values in a nested JSON structure with empty strings.
- **Compare JSON Files**: Compare two JSON files and identify differences in their structures and values.
- **Custom Exceptions**: Handle errors gracefully with custom exception classes.
## Installation

You can install `JSONavigator` using `pip`:

```bash
  pip install JSONavigator
```
Alternatively, if you’re installing from source:

```bash
git clone https://github.com/Nikhil-Singh-2503/JSONavigator.git
cd JSONavigator
```
Create Virtual envirnoment:
```bash
python -m venv venv
source venv/bin/activate
```
Install the requirements:
```bash
pip install -r requirements.txt
```
## Usage/Examples
Here’s how you can use the various features of JSONavigator:

**1. Traverse Nested JSON**

Use the `traverse_json` function to recursively traverse a nested JSON structure and extract paths and values. 

```python
from jsoninja.core import traverse_json

data = {"a": {"b": [1, 2], "c": 3}}

for path, value in traverse_json(data):
    print(f"Path: {path}, Value: {value}")
```

**Output**
```
Path: a.b[0], Value: 1
Path: a.b[1], Value: 2
Path: a.c, Value: 3 
```

**2. Get Value at a Specific Path**

Use the `get_value_at_path` function to retrieve the value at a specific path in the JSON structure.

```python
from jsoninja.core import get_value_at_path

data = {"a": {"b": [1, 2], "c": 3}}
value = get_value_at_path(data, "a.b[1]")
print(value)  # Output: 2
```

**Output**   
`2`

**3. Flatten JSON**

Use the `flatten_json` function to convert a nested JSON structure into a single-level dictionary.

```python
from jsoninja.utils import flatten_json

data = {"a": {"b": [1, 2], "c": 3}}
flattened = flatten_json(data)
print(flattened)
```

**Output**   
```
{
    "a.b[0]": 1,
    "a.b[1]": 2,
    "a.c": 3
}
```
**4. Validate JSON Paths**

Use the `validate_path` function to ensure that a JSON path is properly formatted.

```python
from jsoninja.utils import validate_path
from jsoninja.exceptions import InvalidPathError

try:
    validate_path("a.b[1]")
except InvalidPathError as e:
    print(f"Invalid path: {e}")
```
**Output**   
```
True
```
**5. Format JSON Paths**

Use the `format_path` function to make JSON paths more readable.

```python
from jsoninja.utils import format_path

formatted_path = format_path("a.b[1]")
print(formatted_path)
```
**Output**   
```
a -> b[1]
```

**6. Find Value of an Element**
Use the `find_value_of_element` function to search for a specific key in a nested JSON structure and retrieve its associated value. If the key is not found, the function returns an empty string ("").

```python
from jsoninja.core import find_value_of_element

data = {"a": {"b": {"c": 42}}}
value = find_value_of_element("c", data)
print(value)
```
**Output**   
```
42
```

**7. Empty All Values in a JSON Structure**

Use the `empty_all_the_values` function to replace all values in a nested JSON structure with empty strings (""). For invalid inputs (e.g., integers or strings), the function returns None.

```python
from jsoninja.core import empty_all_the_values

data = {
    "a": 1,
    "b": {"c": 42, "d": [1, 2, {"e": "hello"}]},
    "f": [True, {"g": "world"}],
}
emptied_data = empty_all_the_values(data)
print(emptied_data)
```
**Output**   
```
{
    "a": "",
    "b": {"c": "", "d": ["", "", {"e": ""}]},
    "f": ["", {"g": ""}],
}
```
**8. Compare Two JSON Files**

Use the `compare_files` function to compare two JSON files and identify differences in their structures and values. You can either pass loaded JSON objects or the paths to the JSON files. If you choose to pass file paths, set the `isPath` parameter to `True`.

When using file paths, ensure to use `//` as the path separator, as `/` is treated as an escape character. Alternatively, you can use a raw formatted string (e.g., `r"path/to/file.json"`).

The function returns two values:

1. The actual changes found between the two JSON structures.
2. A summary of the changes.

*Example with Loaded JSON Objects:*

```python
from jsoninja.compare import compare_files

json1 = {"a": {"b": 1, "c": 2}}
json2 = {"a": {"b": 1, "c": 3}}

changes, summary = compare_files(json1, json2)
print("Changes:", changes)
print("Summary:", summary)
```
*Example with File Paths:*

```python
from jsoninja.compare import compare_files
# Use any one of the methods below for specifiying path
file1_path = "path//to//first.json"  # Using // as the path separator
file2_path = r"path/to/second.json"   # Using a raw formatted string

changes, summary = compare_files(file1_path, file2_path, isPath=True)
print("Changes:", changes)
print("Summary:", summary)
```
In this case, ensure that the `isPath` parameter is set to `True` to indicate that you are passing file paths instead of loaded JSON objects

## **Customization**

You can customize the separator used in the functions by passing a value to the `separator` parameter.

**Example**

Suppose you want to use `*` as the separator with the `traverse_json` function.

```python
from jsoninja.core import traverse_json

data = {"a": {"b": [1, 2], "c": 3}}

for path, value in traverse_json(data, seperator=*):
    print(f"Path: {path}, Value: {value}")
```

**Output**
```
Path: a*b[0], Value: 1
Path: a*b[1], Value: 2
Path: a*c, Value: 3 
```
## Contributing

Contributions to JSONavigator are welcome! To contribute: 

- Fork the repository on GitHub.
- Clone your fork locally:
```bash
git clone https://github.com/Nikhil-Singh-2503/JSONavigator.git
```
- Create a new branch for your feature or bugfix:
```bash
git checkout -b feature-name
```
- Make your changes and write tests if applicable.

- Run the tests to ensure everything works:
```bash
pytest
```
- Commit your changes and push them to your fork:
```bash
git commit -m "Add feature or fix"
git push origin feature-name
```
- Open a pull request on the main repository.

## Running Tests

To run the test suite, use `pytest`:

```bash
  pytest
```
For coverage reports, install `pytest-cov` and run:
```bash
  pytest --cov=JSONavigator
```
## License
This project is licensed under the MIT License.



## Contact

If you have any questions or need support, feel free to reach out:

- Email: nikhilraj7654@gmail.com 

## Acknowledgements

- Inspired by the need to simplify working with nested JSON structures.
- Built with ❤️ using Python.
     
## Additional Notes 

- Ensure you have Python 3.8 or higher installed to use this package.
- For more examples and advanced usage, refer to the [Github](https://github.com/Nikhil-Singh-2503) repository .
