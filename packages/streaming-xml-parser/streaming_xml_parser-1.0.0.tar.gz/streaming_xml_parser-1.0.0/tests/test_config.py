"""
Tests for configuration classes (TagConfig and TagState).
"""

import pytest
from xmlstream import TagConfig, TagState, TagBehavior, ConfigurationError


class TestTagConfig:
    """Test TagConfig class functionality."""
    
    def test_init_minimal_streaming(self):
        """Test minimal TagConfig creation for streaming behavior."""
        config = TagConfig('test', TagBehavior.STREAMING)
        assert config.name == 'test'
        assert config.behavior == TagBehavior.STREAMING
        assert config.placeholder_message is None
        assert config.start_callback is None
        assert config.content_callback is None
        assert config.complete_callback is None
    
    def test_init_placeholder_with_message(self):
        """Test TagConfig creation for placeholder behavior with message."""
        config = TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        assert config.name == 'test'
        assert config.behavior == TagBehavior.PLACEHOLDER
        assert config.placeholder_message == 'Loading...'
    
    def test_init_silent(self):
        """Test TagConfig creation for silent behavior."""
        config = TagConfig('test', TagBehavior.SILENT)
        assert config.name == 'test'
        assert config.behavior == TagBehavior.SILENT
        assert config.placeholder_message is None
    
    def test_init_with_callbacks(self):
        """Test TagConfig creation with callbacks."""
        def start_cb(tag): pass
        def content_cb(content): pass
        def complete_cb(tag, content): pass
        
        config = TagConfig(
            'test', 
            TagBehavior.STREAMING,
            start_callback=start_cb,
            content_callback=content_cb,
            complete_callback=complete_cb
        )
        
        assert config.start_callback == start_cb
        assert config.content_callback == content_cb
        assert config.complete_callback == complete_cb
    
    def test_validation_empty_name(self):
        """Test validation fails for empty tag name."""
        with pytest.raises(ConfigurationError, match="Tag name cannot be empty"):
            TagConfig('', TagBehavior.STREAMING)
    
    def test_validation_whitespace_only_name(self):
        """Test validation fails for whitespace-only tag name."""
        with pytest.raises(ConfigurationError, match="Tag name cannot be empty"):
            TagConfig('   ', TagBehavior.STREAMING)
    
    def test_validation_invalid_behavior_type(self):
        """Test validation fails for invalid behavior type."""
        with pytest.raises(ConfigurationError, match="behavior must be a TagBehavior enum"):
            TagConfig('test', 'invalid_behavior')
    
    def test_validation_placeholder_without_message(self):
        """Test validation fails for placeholder behavior without message."""
        with pytest.raises(ConfigurationError, match="placeholder_message is required"):
            TagConfig('test', TagBehavior.PLACEHOLDER)
    
    def test_validation_placeholder_with_empty_message(self):
        """Test validation fails for placeholder behavior with empty message."""
        with pytest.raises(ConfigurationError, match="placeholder_message is required"):
            TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='')
    
    def test_has_callbacks_none(self):
        """Test has_callbacks returns False when no callbacks are set."""
        config = TagConfig('test', TagBehavior.STREAMING)
        assert not config.has_callbacks()
    
    def test_has_callbacks_with_start_callback(self):
        """Test has_callbacks returns True when start callback is set."""
        config = TagConfig('test', TagBehavior.STREAMING, start_callback=lambda x: None)
        assert config.has_callbacks()
    
    def test_has_callbacks_with_content_callback(self):
        """Test has_callbacks returns True when content callback is set."""
        config = TagConfig('test', TagBehavior.STREAMING, content_callback=lambda x: None)
        assert config.has_callbacks()
    
    def test_has_callbacks_with_complete_callback(self):
        """Test has_callbacks returns True when complete callback is set."""
        config = TagConfig('test', TagBehavior.STREAMING, complete_callback=lambda x, y: None)
        assert config.has_callbacks()
    
    def test_validate_callbacks_all_valid(self):
        """Test validate_callbacks with all valid callbacks."""
        config = TagConfig(
            'test', 
            TagBehavior.STREAMING,
            start_callback=lambda x: None,
            content_callback=lambda x: None,
            complete_callback=lambda x, y: None
        )
        assert config.validate_callbacks() is True
    
    def test_validate_callbacks_none_callbacks(self):
        """Test validate_callbacks with no callbacks."""
        config = TagConfig('test', TagBehavior.STREAMING)
        assert config.validate_callbacks() is True
    
    def test_validate_callbacks_invalid_start_callback(self):
        """Test validate_callbacks fails with invalid start callback."""
        with pytest.raises(ConfigurationError, match="start_callback must be callable"):
            TagConfig('test', TagBehavior.STREAMING, start_callback="not_callable")
    
    def test_validate_callbacks_invalid_content_callback(self):
        """Test validate_callbacks fails with invalid content callback."""
        with pytest.raises(ConfigurationError, match="content_callback must be callable"):
            TagConfig('test', TagBehavior.STREAMING, content_callback=123)
    
    def test_validate_callbacks_invalid_complete_callback(self):
        """Test validate_callbacks fails with invalid complete callback."""
        with pytest.raises(ConfigurationError, match="complete_callback must be callable"):
            TagConfig('test', TagBehavior.STREAMING, complete_callback=[])


class TestTagState:
    """Test TagState class functionality."""
    
    def test_init_minimal(self):
        """Test minimal TagState creation."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        assert state.name == 'test'
        assert state.config == config
        assert state.content == ''
        assert state.start_position == 0
    
    def test_init_with_parameters(self):
        """Test TagState creation with all parameters."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config, content='initial', start_position=10)
        
        assert state.name == 'test'
        assert state.config == config
        assert state.content == 'initial'
        assert state.start_position == 10
    
    def test_add_content_new(self):
        """Test adding content to empty state."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        state.add_content('Hello')
        assert state.content == 'Hello'
    
    def test_add_content_append(self):
        """Test appending content to existing content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config, content='Hello')
        
        state.add_content(' World')
        assert state.content == 'Hello World'
    
    def test_add_content_empty_string(self):
        """Test adding empty string doesn't change content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config, content='Hello')
        
        state.add_content('')
        assert state.content == 'Hello'
    
    def test_add_content_none(self):
        """Test adding None doesn't change content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config, content='Hello')
        
        state.add_content(None)
        assert state.content == 'Hello'
    
    def test_get_content_length_empty(self):
        """Test getting content length when empty."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        assert state.get_content_length() == 0
    
    def test_get_content_length_with_content(self):
        """Test getting content length with content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config, content='Hello World')
        
        assert state.get_content_length() == 11
    
    def test_clear_content_empty(self):
        """Test clearing empty content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        cleared = state.clear_content()
        assert cleared == ''
        assert state.content == ''
    
    def test_clear_content_with_content(self):
        """Test clearing content with existing content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config, content='Hello World')
        
        cleared = state.clear_content()
        assert cleared == 'Hello World'
        assert state.content == ''
    
    def test_is_streaming_true(self):
        """Test is_streaming returns True for streaming behavior."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        assert state.is_streaming() is True
    
    def test_is_streaming_false(self):
        """Test is_streaming returns False for non-streaming behavior."""
        config = TagConfig('test', TagBehavior.SILENT)
        state = TagState('test', config)
        
        assert state.is_streaming() is False
    
    def test_is_placeholder_true(self):
        """Test is_placeholder returns True for placeholder behavior."""
        config = TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        state = TagState('test', config)
        
        assert state.is_placeholder() is True
    
    def test_is_placeholder_false(self):
        """Test is_placeholder returns False for non-placeholder behavior."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        assert state.is_placeholder() is False
    
    def test_is_silent_true(self):
        """Test is_silent returns True for silent behavior."""
        config = TagConfig('test', TagBehavior.SILENT)
        state = TagState('test', config)
        
        assert state.is_silent() is True
    
    def test_is_silent_false(self):
        """Test is_silent returns False for non-silent behavior."""
        config = TagConfig('test', TagBehavior.STREAMING)
        state = TagState('test', config)
        
        assert state.is_silent() is False


class TestTagConfigIntegration:
    """Test TagConfig integration scenarios."""
    
    def test_config_with_state_consistency(self):
        """Test that TagConfig and TagState work together consistently."""
        config = TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        state = TagState('test', config)
        
        # Verify consistency between config and state behavior checks
        assert config.behavior == TagBehavior.PLACEHOLDER
        assert state.is_placeholder() is True
        assert state.is_streaming() is False
        assert state.is_silent() is False
    
    def test_callback_integration(self):
        """Test callback integration with tag configuration."""
        callback_called = []
        
        def test_callback(content):
            callback_called.append(content)
        
        config = TagConfig('test', TagBehavior.STREAMING, content_callback=test_callback)
        
        # Verify callback is properly stored and callable
        assert config.has_callbacks() is True
        assert config.validate_callbacks() is True
        assert callable(config.content_callback)
        
        # Test calling the callback
        config.content_callback('test content')
        assert callback_called == ['test content'] 