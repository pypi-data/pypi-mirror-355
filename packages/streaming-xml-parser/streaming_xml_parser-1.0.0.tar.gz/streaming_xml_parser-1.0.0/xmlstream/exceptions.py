"""
Custom exceptions for the streaming XML parser.

This module defines all custom exceptions that can be raised by the
streaming XML parser during operation.
"""


class StreamingXMLError(Exception):
    """
    Base exception class for all streaming XML parser errors.
    
    This is the parent class for all custom exceptions in this package.
    """
    pass


class TagNotFoundError(StreamingXMLError):
    """
    Raised when attempting to operate on a tag that doesn't exist.
    
    This exception is raised when trying to close a tag that was never
    opened or doesn't exist in the current parsing context.
    """
    
    def __init__(self, tag_name: str, message: str = None):
        """
        Initialize the TagNotFoundError.
        
        Args:
            tag_name: The name of the tag that was not found
            message: Optional custom error message
        """
        self.tag_name = tag_name
        if message is None:
            message = f"Tag '{tag_name}' not found in parsing context"
        super().__init__(message)


class InvalidTagError(StreamingXMLError):
    """
    Raised when encountering invalid or malformed XML tags.
    
    This exception is raised when the parser encounters tags that don't
    conform to expected XML syntax or configuration requirements.
    """
    
    def __init__(self, tag_content: str, message: str = None):
        """
        Initialize the InvalidTagError.
        
        Args:
            tag_content: The invalid tag content that caused the error
            message: Optional custom error message
        """
        self.tag_content = tag_content
        if message is None:
            message = f"Invalid tag format: '{tag_content}'"
        super().__init__(message)


class ConfigurationError(StreamingXMLError):
    """
    Raised when there are issues with parser configuration.
    
    This exception is raised when tag configurations are invalid or
    incompatible with the parser's requirements.
    """
    pass


class BufferOverflowError(StreamingXMLError):
    """
    Raised when the internal buffer exceeds safe limits.
    
    This exception is raised as a safety measure when the parser's
    internal buffer grows too large, which could indicate a parsing
    issue or malformed input.
    """
    
    def __init__(self, buffer_size: int, limit: int):
        """
        Initialize the BufferOverflowError.
        
        Args:
            buffer_size: The current size of the buffer
            limit: The maximum allowed buffer size
        """
        self.buffer_size = buffer_size
        self.limit = limit
        message = f"Buffer size {buffer_size} exceeds limit {limit}"
        super().__init__(message)
 