"""
Tests for the exceptions module.
"""

import pytest
from xmlstream import (
    StreamingXMLError,
    TagNotFoundError,
    InvalidTagError,
    ConfigurationError,
    BufferOverflowError
)


class TestStreamingXMLError:
    """Test base StreamingXMLError class."""
    
    def test_is_base_exception(self):
        """Test that StreamingXMLError is the base exception."""
        error = StreamingXMLError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"
    
    def test_inheritance_hierarchy(self):
        """Test that all custom exceptions inherit from StreamingXMLError."""
        # All custom exceptions should inherit from StreamingXMLError
        assert issubclass(TagNotFoundError, StreamingXMLError)
        assert issubclass(InvalidTagError, StreamingXMLError)
        assert issubclass(ConfigurationError, StreamingXMLError)
        assert issubclass(BufferOverflowError, StreamingXMLError)
    
    def test_can_be_raised_and_caught(self):
        """Test that StreamingXMLError can be raised and caught."""
        with pytest.raises(StreamingXMLError) as exc_info:
            raise StreamingXMLError("test error")
        
        assert str(exc_info.value) == "test error"


class TestTagNotFoundError:
    """Test TagNotFoundError class."""
    
    def test_init_with_tag_name_only(self):
        """Test TagNotFoundError initialization with tag name only."""
        error = TagNotFoundError("test_tag")
        assert error.tag_name == "test_tag"
        assert "Tag 'test_tag' not found in parsing context" in str(error)
    
    def test_init_with_custom_message(self):
        """Test TagNotFoundError initialization with custom message."""
        custom_message = "Custom error message"
        error = TagNotFoundError("test_tag", custom_message)
        assert error.tag_name == "test_tag"
        assert str(error) == custom_message
    
    def test_default_message_format(self):
        """Test the default message format."""
        error = TagNotFoundError("missing_tag")
        expected_message = "Tag 'missing_tag' not found in parsing context"
        assert str(error) == expected_message
    
    def test_inheritance(self):
        """Test TagNotFoundError inheritance."""
        error = TagNotFoundError("test")
        assert isinstance(error, StreamingXMLError)
        assert isinstance(error, Exception)
    
    def test_can_be_caught_as_base_exception(self):
        """Test that TagNotFoundError can be caught as StreamingXMLError."""
        with pytest.raises(StreamingXMLError):
            raise TagNotFoundError("test_tag")
    
    def test_tag_name_attribute_access(self):
        """Test that tag_name attribute is accessible."""
        error = TagNotFoundError("my_tag", "custom message")
        assert hasattr(error, 'tag_name')
        assert error.tag_name == "my_tag"


class TestInvalidTagError:
    """Test InvalidTagError class."""
    
    def test_init_with_tag_content_only(self):
        """Test InvalidTagError initialization with tag content only."""
        error = InvalidTagError("<invalid>")
        assert error.tag_content == "<invalid>"
        assert "Invalid tag format: '<invalid>'" in str(error)
    
    def test_init_with_custom_message(self):
        """Test InvalidTagError initialization with custom message."""
        custom_message = "Tag syntax is malformed"
        error = InvalidTagError("<bad>", custom_message)
        assert error.tag_content == "<bad>"
        assert str(error) == custom_message
    
    def test_default_message_format(self):
        """Test the default message format."""
        error = InvalidTagError("< malformed >")
        expected_message = "Invalid tag format: '< malformed >'"
        assert str(error) == expected_message
    
    def test_inheritance(self):
        """Test InvalidTagError inheritance."""
        error = InvalidTagError("test")
        assert isinstance(error, StreamingXMLError)
        assert isinstance(error, Exception)
    
    def test_can_be_caught_as_base_exception(self):
        """Test that InvalidTagError can be caught as StreamingXMLError."""
        with pytest.raises(StreamingXMLError):
            raise InvalidTagError("<invalid>")
    
    def test_tag_content_attribute_access(self):
        """Test that tag_content attribute is accessible."""
        error = InvalidTagError("<test>", "custom message")
        assert hasattr(error, 'tag_content')
        assert error.tag_content == "<test>"
    
    def test_with_empty_tag_content(self):
        """Test InvalidTagError with empty tag content."""
        error = InvalidTagError("")
        assert error.tag_content == ""
        assert "Invalid tag format: ''" in str(error)


class TestConfigurationError:
    """Test ConfigurationError class."""
    
    def test_init_with_message(self):
        """Test ConfigurationError initialization."""
        message = "Invalid configuration detected"
        error = ConfigurationError(message)
        assert str(error) == message
    
    def test_inheritance(self):
        """Test ConfigurationError inheritance."""
        error = ConfigurationError("test")
        assert isinstance(error, StreamingXMLError)
        assert isinstance(error, Exception)
    
    def test_can_be_caught_as_base_exception(self):
        """Test that ConfigurationError can be caught as StreamingXMLError."""
        with pytest.raises(StreamingXMLError):
            raise ConfigurationError("config error")
    
    def test_empty_message(self):
        """Test ConfigurationError with empty message."""
        error = ConfigurationError("")
        assert str(error) == ""
    
    def test_typical_usage_scenarios(self):
        """Test typical usage scenarios for ConfigurationError."""
        # Test various configuration error scenarios
        scenarios = [
            "Tag name cannot be empty",
            "behavior must be a TagBehavior enum",
            "placeholder_message is required for PLACEHOLDER behavior",
            "start_callback must be callable"
        ]
        
        for message in scenarios:
            error = ConfigurationError(message)
            assert str(error) == message
            assert isinstance(error, StreamingXMLError)


class TestBufferOverflowError:
    """Test BufferOverflowError class."""
    
    def test_init_with_sizes(self):
        """Test BufferOverflowError initialization with buffer sizes."""
        error = BufferOverflowError(2048, 1024)
        assert error.buffer_size == 2048
        assert error.limit == 1024
        expected_message = "Buffer size 2048 exceeds limit 1024"
        assert str(error) == expected_message
    
    def test_buffer_size_attribute_access(self):
        """Test buffer size attributes are accessible."""
        error = BufferOverflowError(5000, 4096)
        assert hasattr(error, 'buffer_size')
        assert hasattr(error, 'limit')
        assert error.buffer_size == 5000
        assert error.limit == 4096
    
    def test_inheritance(self):
        """Test BufferOverflowError inheritance."""
        error = BufferOverflowError(100, 50)
        assert isinstance(error, StreamingXMLError)
        assert isinstance(error, Exception)
    
    def test_can_be_caught_as_base_exception(self):
        """Test that BufferOverflowError can be caught as StreamingXMLError."""
        with pytest.raises(StreamingXMLError):
            raise BufferOverflowError(200, 100)
    
    def test_message_format(self):
        """Test the message format with different values."""
        test_cases = [
            (100, 50, "Buffer size 100 exceeds limit 50"),
            (1024, 512, "Buffer size 1024 exceeds limit 512"),
            (0, 0, "Buffer size 0 exceeds limit 0")
        ]
        
        for buffer_size, limit, expected_message in test_cases:
            error = BufferOverflowError(buffer_size, limit)
            assert str(error) == expected_message
    
    def test_large_numbers(self):
        """Test BufferOverflowError with large numbers."""
        large_buffer = 1024 * 1024 * 10  # 10MB
        large_limit = 1024 * 1024 * 5    # 5MB
        
        error = BufferOverflowError(large_buffer, large_limit)
        assert error.buffer_size == large_buffer
        assert error.limit == large_limit
        assert f"Buffer size {large_buffer} exceeds limit {large_limit}" in str(error)


class TestExceptionIntegration:
    """Test exception integration scenarios."""
    
    def test_catching_all_custom_exceptions(self):
        """Test catching all custom exceptions with base class."""
        exceptions_to_test = [
            TagNotFoundError("test"),
            InvalidTagError("<test>"),
            ConfigurationError("test"),
            BufferOverflowError(100, 50)
        ]
        
        for exception in exceptions_to_test:
            with pytest.raises(StreamingXMLError):
                raise exception
    
    def test_exception_chaining(self):
        """Test exception chaining scenarios."""
        try:
            try:
                raise TagNotFoundError("inner_tag")
            except TagNotFoundError as e:
                raise ConfigurationError("Configuration failed") from e
        except ConfigurationError as e:
            assert isinstance(e.__cause__, TagNotFoundError)
            assert e.__cause__.tag_name == "inner_tag"
    
    def test_exception_in_typical_parsing_context(self):
        """Test exceptions in typical parsing context."""
        # Simulate parser encountering various errors
        
        # Tag not found scenario
        with pytest.raises(TagNotFoundError) as exc_info:
            raise TagNotFoundError("missing_closing_tag")
        assert "missing_closing_tag" in str(exc_info.value)
        
        # Invalid tag scenario
        with pytest.raises(InvalidTagError) as exc_info:
            raise InvalidTagError("<>")
        assert "Invalid tag format" in str(exc_info.value)
        
        # Buffer overflow scenario
        with pytest.raises(BufferOverflowError) as exc_info:
            raise BufferOverflowError(2048, 1024)
        assert exc_info.value.buffer_size == 2048
        assert exc_info.value.limit == 1024
    
    def test_exception_messages_are_helpful(self):
        """Test that exception messages provide helpful debugging information."""
        # TagNotFoundError should include tag name
        tag_error = TagNotFoundError("user_data")
        assert "user_data" in str(tag_error)
        
        # InvalidTagError should include problematic content
        invalid_error = InvalidTagError("<unclosed")
        assert "<unclosed" in str(invalid_error)
        
        # BufferOverflowError should include both sizes
        buffer_error = BufferOverflowError(5000, 4096)
        error_message = str(buffer_error)
        assert "5000" in error_message
        assert "4096" in error_message
    
    def test_all_exceptions_are_properly_defined(self):
        """Test that all exceptions are properly defined and importable."""
        # Verify all exceptions can be imported and instantiated
        exceptions = [
            StreamingXMLError,
            TagNotFoundError,
            InvalidTagError,
            ConfigurationError,
            BufferOverflowError
        ]
        
        for exc_class in exceptions:
            # Should be able to create instance
            if exc_class == TagNotFoundError:
                instance = exc_class("test_tag")
            elif exc_class == InvalidTagError:
                instance = exc_class("<test>")
            elif exc_class == BufferOverflowError:
                instance = exc_class(100, 50)
            else:
                instance = exc_class("test message")
            
            # Should be proper exception
            assert isinstance(instance, Exception)
            assert isinstance(instance, StreamingXMLError) 