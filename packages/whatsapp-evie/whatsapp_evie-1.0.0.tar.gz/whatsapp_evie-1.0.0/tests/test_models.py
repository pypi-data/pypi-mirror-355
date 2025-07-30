"""
Tests for WhatsApp-Evie models.
"""

import pytest
import time
from pydantic import ValidationError

from whatsapp_evie.models import (
    Message, MessageType, MessageStatus, MediaInfo, LocationInfo, 
    ContactInfo, InteractiveButton, InteractiveContent
)


class TestMessage:
    """Test Message model."""
    
    def test_create_text_message(self):
        """Test creating a text message."""
        message = Message.create_text(
            content="Hello, World!",
            recipient_id="+1234567890",
            sender_id="test_sender"
        )
        
        assert message.type == MessageType.TEXT
        assert message.content == "Hello, World!"
        assert message.recipient_id == "+1234567890"
        assert message.sender_id == "test_sender"
        assert message.status == MessageStatus.PENDING
        assert message.message_id is not None
        assert isinstance(message.timestamp, float)
    
    def test_create_media_message(self):
        """Test creating a media message."""
        message = Message.create_media(
            media_type=MessageType.IMAGE,
            url="https://example.com/image.jpg",
            recipient_id="+1234567890",
            caption="Test image"
        )
        
        assert message.type == MessageType.IMAGE
        assert message.content == "https://example.com/image.jpg"
        assert message.media_info is not None
        assert message.media_info.url == "https://example.com/image.jpg"
        assert message.media_info.caption == "Test image"
    
    def test_create_location_message(self):
        """Test creating a location message."""
        message = Message.create_location(
            latitude=37.7749,
            longitude=-122.4194,
            recipient_id="+1234567890",
            name="San Francisco",
            address="San Francisco, CA"
        )
        
        assert message.type == MessageType.LOCATION
        assert message.location_info is not None
        assert message.location_info.latitude == 37.7749
        assert message.location_info.longitude == -122.4194
        assert message.location_info.name == "San Francisco"
    
    def test_create_contact_message(self):
        """Test creating a contact message."""
        message = Message.create_contact(
            name="John Doe",
            recipient_id="+1234567890",
            phone="+0987654321",
            email="john@example.com"
        )
        
        assert message.type == MessageType.CONTACT
        assert message.contact_info is not None
        assert message.contact_info.name == "John Doe"
        assert message.contact_info.phone == "+0987654321"
        assert message.contact_info.email == "john@example.com"
    
    def test_message_validation(self):
        """Test message validation."""
        # Test invalid phone number
        with pytest.raises(ValidationError):
            Message.create_text(
                content="Hello",
                recipient_id="invalid_phone",
                sender_id="test"
            )
        
        # Test empty content for text message
        with pytest.raises(ValidationError):
            Message(
                type=MessageType.TEXT,
                content="",
                recipient_id="+1234567890",
                sender_id="test"
            )
    
    def test_content_sanitization(self):
        """Test content sanitization."""
        message = Message.create_text(
            content="Hello\x00World\x01!",  # Contains null bytes
            recipient_id="+1234567890"
        )
        
        assert "\x00" not in message.content
        assert "\x01" not in message.content
        assert message.content == "HelloWorld!"
    
    def test_to_whatsapp_payload_text(self):
        """Test converting text message to WhatsApp payload."""
        message = Message.create_text(
            content="Hello, World!",
            recipient_id="+1234567890"
        )
        
        payload = message.to_whatsapp_payload()
        
        assert payload["messaging_product"] == "whatsapp"
        assert payload["recipient_type"] == "individual"
        assert payload["to"] == "+1234567890"
        assert payload["type"] == "text"
        assert payload["text"]["body"] == "Hello, World!"
    
    def test_to_whatsapp_payload_image(self):
        """Test converting image message to WhatsApp payload."""
        message = Message.create_media(
            media_type=MessageType.IMAGE,
            url="https://example.com/image.jpg",
            recipient_id="+1234567890",
            caption="Test image"
        )
        
        payload = message.to_whatsapp_payload()
        
        assert payload["type"] == "image"
        assert payload["image"]["link"] == "https://example.com/image.jpg"
        assert payload["image"]["caption"] == "Test image"
    
    def test_to_whatsapp_payload_location(self):
        """Test converting location message to WhatsApp payload."""
        message = Message.create_location(
            latitude=37.7749,
            longitude=-122.4194,
            recipient_id="+1234567890",
            name="San Francisco"
        )
        
        payload = message.to_whatsapp_payload()
        
        assert payload["type"] == "location"
        assert payload["location"]["latitude"] == 37.7749
        assert payload["location"]["longitude"] == -122.4194
        assert payload["location"]["name"] == "San Francisco"


class TestMediaInfo:
    """Test MediaInfo model."""
    
    def test_media_info_creation(self):
        """Test creating MediaInfo."""
        media_info = MediaInfo(
            url="https://example.com/image.jpg",
            media_id="media_123",
            filename="image.jpg",
            mime_type="image/jpeg",
            file_size=1024,
            caption="Test image"
        )
        
        assert media_info.url == "https://example.com/image.jpg"
        assert media_info.media_id == "media_123"
        assert media_info.filename == "image.jpg"
        assert media_info.mime_type == "image/jpeg"
        assert media_info.file_size == 1024
        assert media_info.caption == "Test image"
    
    def test_caption_sanitization(self):
        """Test caption sanitization."""
        media_info = MediaInfo(
            url="https://example.com/image.jpg",
            caption="Hello\x00World!"
        )
        
        assert "\x00" not in media_info.caption
        assert media_info.caption == "HelloWorld!"


class TestLocationInfo:
    """Test LocationInfo model."""
    
    def test_location_info_creation(self):
        """Test creating LocationInfo."""
        location_info = LocationInfo(
            latitude=37.7749,
            longitude=-122.4194,
            name="San Francisco",
            address="San Francisco, CA"
        )
        
        assert location_info.latitude == 37.7749
        assert location_info.longitude == -122.4194
        assert location_info.name == "San Francisco"
        assert location_info.address == "San Francisco, CA"


class TestContactInfo:
    """Test ContactInfo model."""
    
    def test_contact_info_creation(self):
        """Test creating ContactInfo."""
        contact_info = ContactInfo(
            name="John Doe",
            phone="+1234567890",
            email="john@example.com",
            organization="Example Corp"
        )
        
        assert contact_info.name == "John Doe"
        assert contact_info.phone == "+1234567890"
        assert contact_info.email == "john@example.com"
        assert contact_info.organization == "Example Corp"
    
    def test_phone_validation(self):
        """Test phone number validation."""
        # Valid phone number
        contact_info = ContactInfo(
            name="John Doe",
            phone="+1234567890"
        )
        assert contact_info.phone == "+1234567890"
        
        # Invalid phone number
        with pytest.raises(ValidationError):
            ContactInfo(
                name="John Doe",
                phone="invalid"
            )


class TestInteractiveContent:
    """Test InteractiveContent model."""
    
    def test_interactive_button_creation(self):
        """Test creating interactive button."""
        button = InteractiveButton(
            id="button_1",
            title="Click Me"
        )
        
        assert button.id == "button_1"
        assert button.title == "Click Me"
        assert button.type == "reply"
    
    def test_interactive_content_creation(self):
        """Test creating interactive content."""
        buttons = [
            InteractiveButton(id="yes", title="Yes"),
            InteractiveButton(id="no", title="No")
        ]
        
        content = InteractiveContent(
            type="button",
            header="Question",
            body="Do you want to continue?",
            footer="Choose an option",
            buttons=buttons
        )
        
        assert content.type == "button"
        assert content.header == "Question"
        assert content.body == "Do you want to continue?"
        assert content.footer == "Choose an option"
        assert len(content.buttons) == 2
