"""
Tests for the event system (StreamingEvent and EventType).
"""

import pytest
from xmlstream import StreamingEvent, EventType, TagConfig, TagBehavior


class TestStreamingEvent:
    """Test StreamingEvent class functionality."""
    
    def test_init_minimal(self):
        """Test minimal StreamingEvent creation."""
        event = StreamingEvent(EventType.CONTENT)
        assert event.event_type == EventType.CONTENT
        assert event.tag_name is None
        assert event.content is None
        assert event.data is None
    
    def test_init_content_event(self):
        """Test StreamingEvent creation for content."""
        event = StreamingEvent(EventType.CONTENT, content="Hello World")
        assert event.event_type == EventType.CONTENT
        assert event.content == "Hello World"
        assert event.tag_name is None
        assert event.data is None
    
    def test_init_tag_start_event(self):
        """Test StreamingEvent creation for tag start."""
        config = TagConfig('test', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_START, tag_name='test', data=config)
        assert event.event_type == EventType.TAG_START
        assert event.tag_name == 'test'
        assert event.data == config
        assert event.content is None
    
    def test_init_tag_content_event(self):
        """Test StreamingEvent creation for tag content."""
        config = TagConfig('test', TagBehavior.STREAMING)
        event = StreamingEvent(
            EventType.TAG_CONTENT, 
            tag_name='test', 
            content='streaming content',
            data=config
        )
        assert event.event_type == EventType.TAG_CONTENT
        assert event.tag_name == 'test'
        assert event.content == 'streaming content'
        assert event.data == config
    
    def test_init_tag_complete_event(self):
        """Test StreamingEvent creation for tag complete."""
        config = TagConfig('test', TagBehavior.PLACEHOLDER, placeholder_message='Loading...')
        event = StreamingEvent(
            EventType.TAG_COMPLETE,
            tag_name='test',
            content='complete content',
            data=config
        )
        assert event.event_type == EventType.TAG_COMPLETE
        assert event.tag_name == 'test'
        assert event.content == 'complete content'
        assert event.data == config
    
    def test_init_all_parameters(self):
        """Test StreamingEvent creation with all parameters."""
        config = TagConfig('test', TagBehavior.SILENT)
        event = StreamingEvent(
            event_type=EventType.TAG_CONTENT,
            tag_name='test',
            content='test content',
            data=config
        )
        assert event.event_type == EventType.TAG_CONTENT
        assert event.tag_name == 'test'
        assert event.content == 'test content'
        assert event.data == config
    
    def test_init_invalid_event_type(self):
        """Test StreamingEvent validation fails for invalid event type."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            StreamingEvent("invalid_type")
    
    def test_init_empty_string_event_type(self):
        """Test StreamingEvent validation fails for empty event type."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            StreamingEvent("")
    
    def test_is_content_event_true_content(self):
        """Test is_content_event returns True for content events."""
        event = StreamingEvent(EventType.CONTENT, content="test")
        assert event.is_content_event() is True
    
    def test_is_content_event_true_tag_content(self):
        """Test is_content_event returns True for tag content events."""
        event = StreamingEvent(EventType.TAG_CONTENT, tag_name='test', content="test")
        assert event.is_content_event() is True
    
    def test_is_content_event_false_tag_start(self):
        """Test is_content_event returns False for tag start events."""
        event = StreamingEvent(EventType.TAG_START, tag_name='test')
        assert event.is_content_event() is False
    
    def test_is_content_event_false_tag_complete(self):
        """Test is_content_event returns False for tag complete events."""
        event = StreamingEvent(EventType.TAG_COMPLETE, tag_name='test')
        assert event.is_content_event() is False
    
    def test_is_tag_event_true_tag_start(self):
        """Test is_tag_event returns True for tag start events."""
        event = StreamingEvent(EventType.TAG_START, tag_name='test')
        assert event.is_tag_event() is True
    
    def test_is_tag_event_true_tag_complete(self):
        """Test is_tag_event returns True for tag complete events."""
        event = StreamingEvent(EventType.TAG_COMPLETE, tag_name='test')
        assert event.is_tag_event() is True
    
    def test_is_tag_event_false_content(self):
        """Test is_tag_event returns False for content events."""
        event = StreamingEvent(EventType.CONTENT, content="test")
        assert event.is_tag_event() is False
    
    def test_is_tag_event_false_tag_content(self):
        """Test is_tag_event returns False for tag content events."""
        event = StreamingEvent(EventType.TAG_CONTENT, tag_name='test', content="test")
        assert event.is_tag_event() is False
    
    def test_has_content_true_with_content(self):
        """Test has_content returns True when content exists."""
        event = StreamingEvent(EventType.CONTENT, content="Hello")
        assert event.has_content() is True
    
    def test_has_content_false_with_empty_content(self):
        """Test has_content returns False with empty content."""
        event = StreamingEvent(EventType.CONTENT, content="")
        assert event.has_content() is False
    
    def test_has_content_false_with_none_content(self):
        """Test has_content returns False with None content."""
        event = StreamingEvent(EventType.TAG_START, tag_name='test', content=None)
        assert event.has_content() is False
    
    def test_has_content_false_with_no_content(self):
        """Test has_content returns False when content is not set."""
        event = StreamingEvent(EventType.TAG_START, tag_name='test')
        assert event.has_content() is False
    
    def test_immutability(self):
        """Test that StreamingEvent is immutable (frozen dataclass)."""
        event = StreamingEvent(EventType.CONTENT, content="test")
        
        # Attempting to modify should raise an exception
        with pytest.raises(AttributeError):
            event.content = "modified"
        
        with pytest.raises(AttributeError):
            event.event_type = EventType.TAG_START


class TestEventType:
    """Test EventType constants and utilities."""
    
    def test_constants_values(self):
        """Test EventType constant values."""
        assert EventType.CONTENT == "content"
        assert EventType.TAG_START == "tag_start"
        assert EventType.TAG_CONTENT == "tag_content"
        assert EventType.TAG_COMPLETE == "tag_complete"
    
    def test_all_types_method(self):
        """Test EventType.all_types() method."""
        all_types = EventType.all_types()
        
        assert isinstance(all_types, set)
        assert len(all_types) == 4
        assert EventType.CONTENT in all_types
        assert EventType.TAG_START in all_types
        assert EventType.TAG_CONTENT in all_types
        assert EventType.TAG_COMPLETE in all_types
    
    def test_all_types_immutable(self):
        """Test that all_types() returns a fresh set each time."""
        types1 = EventType.all_types()
        types2 = EventType.all_types()
        
        # Should be equal but not the same object
        assert types1 == types2
        assert types1 is not types2
        
        # Modifying one shouldn't affect the other
        types1.add("custom_type")
        assert "custom_type" not in types2


class TestEventIntegration:
    """Test event system integration scenarios."""
    
    def test_event_with_tag_config_data(self):
        """Test events carrying TagConfig as data."""
        config = TagConfig('stream', TagBehavior.STREAMING)
        event = StreamingEvent(EventType.TAG_START, tag_name='stream', data=config)
        
        assert event.data == config
        assert event.data.behavior == TagBehavior.STREAMING
        assert event.tag_name == config.name
    
    def test_event_lifecycle_sequence(self):
        """Test a complete event lifecycle for a tag."""
        config = TagConfig('test', TagBehavior.STREAMING)
        
        # Start event
        start_event = StreamingEvent(EventType.TAG_START, tag_name='test', data=config)
        assert start_event.event_type == EventType.TAG_START
        assert start_event.tag_name == 'test'
        assert not start_event.has_content()
        
        # Content event
        content_event = StreamingEvent(
            EventType.TAG_CONTENT, 
            tag_name='test', 
            content='streaming data',
            data=config
        )
        assert content_event.event_type == EventType.TAG_CONTENT
        assert content_event.has_content()
        assert content_event.content == 'streaming data'
        
        # Complete event
        complete_event = StreamingEvent(
            EventType.TAG_COMPLETE,
            tag_name='test',
            content='all content',
            data=config
        )
        assert complete_event.event_type == EventType.TAG_COMPLETE
        assert complete_event.has_content()
        assert complete_event.content == 'all content'
    
    def test_event_validation_with_various_data_types(self):
        """Test events can carry various data types."""
        # String data
        event1 = StreamingEvent(EventType.CONTENT, content="test", data="string_data")
        assert event1.data == "string_data"
        
        # Dict data
        event2 = StreamingEvent(EventType.CONTENT, content="test", data={"key": "value"})
        assert event2.data == {"key": "value"}
        
        # Custom object data
        config = TagConfig('test', TagBehavior.SILENT)
        event3 = StreamingEvent(EventType.TAG_START, tag_name='test', data=config)
        assert isinstance(event3.data, TagConfig)
        assert event3.data.name == 'test'
    
    def test_event_string_representation(self):
        """Test event string representation for debugging."""
        event = StreamingEvent(
            EventType.TAG_CONTENT,
            tag_name='test',
            content='sample content'
        )
        
        # Should be able to convert to string without error
        str_repr = str(event)
        assert isinstance(str_repr, str)
        assert 'TAG_CONTENT' in str_repr or 'tag_content' in str_repr
    
    def test_event_equality(self):
        """Test event equality comparison."""
        config = TagConfig('test', TagBehavior.STREAMING)
        
        event1 = StreamingEvent(
            EventType.TAG_START,
            tag_name='test',
            data=config
        )
        
        event2 = StreamingEvent(
            EventType.TAG_START,
            tag_name='test',
            data=config
        )
        
        # Events with same values should be equal
        assert event1 == event2
        
        # Events with different values should not be equal
        event3 = StreamingEvent(
            EventType.TAG_COMPLETE,
            tag_name='test',
            data=config
        )
        
        assert event1 != event3 