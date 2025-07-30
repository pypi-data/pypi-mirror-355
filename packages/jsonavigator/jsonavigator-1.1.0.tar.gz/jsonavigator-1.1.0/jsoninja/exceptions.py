class NestedJSONUtilsError(Exception):
    """Base class for all exceptions in the nested_json_utils package."""
    pass


class InvalidPathError(NestedJSONUtilsError):
    """Raised when an invalid path is provided."""
    def __init__(self, message="Invalid path provided."):
        super().__init__(message)


class ElementNotFoundError(NestedJSONUtilsError):
    """Raised when the target element is not found in the JSON structure."""
    def __init__(self, element, message="Element not found in JSON structure."):
        self.element = element
        super().__init__(f"{message} Element: {element}")


class JSONStructureError(NestedJSONUtilsError):
    """Raised when there is an issue with the JSON structure."""
    def __init__(self, message="Invalid JSON structure."):
        super().__init__(message)