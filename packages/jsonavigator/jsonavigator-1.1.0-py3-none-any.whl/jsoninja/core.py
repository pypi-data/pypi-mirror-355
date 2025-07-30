import re
def traverse_json(data, parent_key='', separator='.'):
    """
    Recursively traverse a nested JSON structure and yield paths and values.
    :param data: The JSON data (dict or list).
    :param parent_key: The accumulated key path.
    :param separator: The separator to join keys.
    :yield: (path, value) tuples.
    """
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                yield from traverse_json(value, new_key, separator)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                new_key = f"{parent_key}[{index}]"
                yield from traverse_json(value, new_key, separator)
        else:
            yield parent_key, data
    except Exception as e:
        print(e)


def get_value_at_path(data, path, separator='.'):
    """
    Get the value at a given path in the JSON structure.
    :param data: The JSON data (dict or list).
    :param path: The path to the desired element.
    :param separator: The separator used in the path.
    :return: The value at the given path.
    """
    try:
        # Regular expression to match keys (e.g., "a") and indices (e.g., "[1]")
        pattern = re.compile(rf'[^{re.escape(separator)}\[\]]+|\[\d+\]')
        
        # Split the path into components
        components = pattern.findall(path)
        current = data
        
        for component in components:
            if component.startswith('[') and component.endswith(']'):
                # Extract the index from the brackets
                index = int(component[1:-1])
                if isinstance(current, list):
                    current = current[index]
                else:
                    raise KeyError(f"Index {index} accessed on non-list: {current}")
            else:
                # Access the key in the dictionary
                if isinstance(current, dict):
                    current = current[component]
                else:
                    raise KeyError(f"Key {component} accessed on non-dictionary: {current}")
        
        return current
    except Exception as e:
        print(e)


def find_all_paths_for_element(file_data, target_key, path='', separator='.'):
    """
    Find all paths where the target key exists.
    :param file_data: The JSON data (dict or list).
    :param target_key: The target key to search for.
    :param path: The accumulated path so far.
    :param separator: The separator used in paths.
    :return: List of paths where the target key is found.
    """
    try:
        result = []
        if isinstance(file_data, dict):
            for key, value in file_data.items():
                new_path = f"{path}{separator}{key}" if path else key
                if key == target_key:
                    result.append(new_path)
                if isinstance(value, (dict, list)):
                    result.extend(find_all_paths_for_element(value, target_key, new_path, separator))

        elif isinstance(file_data, list):
            for index, item in enumerate(file_data):
                new_path = f"{path}[{index}]"
                result.extend(find_all_paths_for_element(item, target_key, new_path, separator))

        return result
    except Exception as e:
        print(e)

def find_value_of_element(target_key, data):
    """
    Recursively searches for the first occurrence of the target_key in the nested data structure (dict or list).
    Returns the value associated with the target_key or None if not found.
    """
    try:
        if isinstance(data, dict):
            if target_key in data:
                return data[target_key]  # Return the value immediately if found
            
            for value in data.values():
                result = find_value_of_element(target_key, value)
                if result:  # If a match is found in the recursion, return it
                    return result
        
        elif isinstance(data, list):
            for item in data:
                result = find_value_of_element(target_key, item)
                if result:  # If a match is found in the recursion, return it
                    return result
        # If no match is found, return None
        return ''
    except Exception as e:
        print(e)
        return ''
    
def empty_all_the_values(data):
    """
    Recursively empties all values in a nested JSON structure.
    :param data: The JSON data (dict or list).
    :return: The modified data with all values replaced by empty strings, or None for invalid inputs.
    """
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    empty_all_the_values(value)
                else:
                    data[key] = ""
            return data

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    empty_all_the_values(item)
                else:
                    data[i] = ""
            return data

        # Return None for non-dict/non-list inputs
        return None

    except Exception as e:
        print(e)
        return None
