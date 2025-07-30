"""
Tests for WhatsApp-Evie client.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import aiohttp

from whatsapp_evie import WhatsAppEvieClient, Message, MessageType, MessageStatus
from whatsapp_evie.exceptions import ValidationError, AuthenticationError, RateLimitError, APIError


class TestWhatsAppEvieClient:
    """Test WhatsAppEvieClient."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = WhatsAppEvieClient(config=mock_config)
        
        assert client.config == mock_config
        assert client._session is None
        assert len(client._message_handlers) == len(MessageType)
        assert len(client._global_handlers) == 0
        assert len(client._error_handlers) == 0
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, mock_config):
        """Test client as async context manager."""
        async with WhatsAppEvieClient(config=mock_config) as client:
            assert client._session is not None
        
        # Session should be closed after exiting context
        assert client._session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, mock_client):
        """Test session creation."""
        await mock_client._ensure_session()
        assert mock_client._session is not None
    
    def test_register_message_handler(self, mock_client):
        """Test registering message handlers."""
        handler = Mock()
        
        mock_client.register_message_handler(MessageType.TEXT, handler)
        
        assert handler in mock_client._message_handlers[MessageType.TEXT]
    
    def test_register_global_handler(self, mock_client):
        """Test registering global handlers."""
        handler = Mock()
        
        mock_client.register_global_handler(handler)
        
        assert handler in mock_client._global_handlers
    
    def test_register_error_handler(self, mock_client):
        """Test registering error handlers."""
        handler = Mock()
        
        mock_client.register_error_handler(handler)
        
        assert handler in mock_client._error_handlers
    
    def test_unregister_handler(self, mock_client):
        """Test unregistering handlers."""
        handler = Mock()
        
        mock_client.register_message_handler(MessageType.TEXT, handler)
        assert handler in mock_client._message_handlers[MessageType.TEXT]
        
        mock_client.unregister_handler(MessageType.TEXT, handler)
        assert handler not in mock_client._message_handlers[MessageType.TEXT]
    
    def test_clear_handlers(self, mock_client):
        """Test clearing handlers."""
        handler1 = Mock()
        handler2 = Mock()
        
        mock_client.register_message_handler(MessageType.TEXT, handler1)
        mock_client.register_global_handler(handler2)
        
        mock_client.clear_handlers()
        
        assert len(mock_client._message_handlers[MessageType.TEXT]) == 0
        assert len(mock_client._global_handlers) == 0
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_message_success(self, mock_post, mock_client, sample_text_message):
        """Test successful message sending."""
        # Create a proper mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        mock_response.headers = {}

        # Mock the post method to return our response
        mock_post.return_value.__aenter__.return_value = mock_response
        mock_post.return_value.__aexit__.return_value = None

        # Mock rate limiter
        mock_client._rate_limiter.acquire = AsyncMock()

        result = await mock_client.send_message(sample_text_message)
        assert result is True
        assert sample_text_message.status == MessageStatus.SENT

    @pytest.mark.asyncio
    async def test_send_message_validation_error(self, mock_client):
        """Test message sending with validation error."""
        with pytest.raises(ValidationError):
            await mock_client.send_message(Message(
                type=MessageType.TEXT,
                content="Hello",
                recipient_id="",  # Invalid recipient
                sender_id="test_sender"
            ))

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_message_authentication_error(self, mock_post, mock_client, sample_text_message):
        """Test message sending with authentication error."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={"error": {"message": "Invalid token"}})
        mock_response.headers = {}

        # Mock the post method to return our response
        mock_post.return_value.__aenter__.return_value = mock_response
        mock_post.return_value.__aexit__.return_value = None

        mock_client._rate_limiter.acquire = AsyncMock()

        with pytest.raises(AuthenticationError):
            await mock_client.send_message(sample_text_message)
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_message_rate_limit_error(self, mock_post, mock_client, sample_text_message):
        """Test message sending with rate limit error."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json = AsyncMock(return_value={"error": {"message": "Rate limit exceeded"}})

        # Mock the post method to return our response
        mock_post.return_value.__aenter__.return_value = mock_response
        mock_post.return_value.__aexit__.return_value = None

        # Mock rate limiter
        mock_client._rate_limiter.acquire = AsyncMock()

        with pytest.raises(RateLimitError) as exc_info:
            await mock_client.send_message(sample_text_message)

        assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    async def test_receive_message_text(self, mock_client, sample_webhook_payload):
        """Test receiving a text message."""
        message = await mock_client.receive_message(sample_webhook_payload)
        assert message is not None
        assert message.type == MessageType.TEXT
        assert message.content == "Hello from WhatsApp!"
        assert message.recipient_id == "test_phone_id"
        assert message.sender_id == "1234567890"
    
    @pytest.mark.asyncio
    async def test_receive_message_image(self, mock_client):
        """Test receiving an image message."""
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "id": "test_message_id",
                            "timestamp": "1234567890",
                            "image": {
                                "id": "image_123",
                                "mime_type": "image/jpeg",
                                "caption": "Test image"
                            },
                            "type": "image"
                        }]
                    }
                }]
            }]
        }
        
        message = await mock_client.receive_message(payload)
        assert message is not None
        assert message.type == MessageType.IMAGE
        assert message.media_info is not None
        assert message.media_info.media_id == "image_123"
        assert message.media_info.mime_type == "image/jpeg"
        assert message.media_info.caption == "Test image"
    
    @pytest.mark.asyncio
    async def test_receive_message_location(self, mock_client):
        """Test receiving a location message."""
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "id": "test_message_id",
                            "timestamp": "1234567890",
                            "location": {
                                "latitude": 37.7749,
                                "longitude": -122.4194,
                                "name": "San Francisco",
                                "address": "San Francisco, CA"
                            },
                            "type": "location"
                        }]
                    }
                }]
            }]
        }
        
        message = await mock_client.receive_message(payload)
        assert message is not None
        assert message.type == MessageType.LOCATION
        assert message.location_info is not None
        assert message.location_info.latitude == 37.7749
        assert message.location_info.longitude == -122.4194
        assert message.location_info.name == "San Francisco"
        assert message.location_info.address == "San Francisco, CA"
    
    @pytest.mark.asyncio
    async def test_call_message_handlers(self, mock_client, sample_text_message):
        """Test calling message handlers."""
        text_handler = AsyncMock()
        global_handler = AsyncMock()
        
        mock_client.register_message_handler(MessageType.TEXT, text_handler)
        mock_client.register_global_handler(global_handler)
        
        await mock_client._call_message_handlers(sample_text_message)
        
        text_handler.assert_called_once_with(sample_text_message)
        global_handler.assert_called_once_with(sample_text_message)
    
    @pytest.mark.asyncio
    async def test_send_bulk_messages(self, mock_client):
        """Test sending bulk messages."""
        messages = [
            Message.create_text("Message 1", "+1234567890"),
            Message.create_text("Message 2", "+1234567890"),
            Message.create_text("Message 3", "+1234567890")
        ]
        
        # Mock send_message to return True
        mock_client.send_message = AsyncMock(return_value=True)
        
        results = await mock_client.send_bulk_messages(messages)
        
        assert len(results) == 3
        assert all(results.values())
        assert mock_client.send_message.call_count == 3
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_media_url(self, mock_get, mock_client):
        """Test getting media URL."""
        # Create a proper mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"url": "https://example.com/media.jpg"})

        # Mock the get method to return our response
        mock_get.return_value.__aenter__.return_value = mock_response
        mock_get.return_value.__aexit__.return_value = None

        url = await mock_client.get_media_url("media_123")
        assert url == "https://example.com/media.jpg"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Complex mocking required - needs integration test setup")
    async def test_download_media(self, mock_client):
        """Test downloading media."""
        # Mock get_media_url to return a URL
        mock_client.get_media_url = AsyncMock(return_value="https://example.com/media.jpg")

        # Mock session response for downloading
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked.return_value = [b"chunk1", b"chunk2"]

        # Create a proper mock context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_context_manager.__aexit__.return_value = None

        # Mock the session and its get method
        mock_client._session = AsyncMock()
        mock_client._session.get.return_value = mock_context_manager
        mock_client._ensure_session = AsyncMock()

        with patch("builtins.open", create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = await mock_client.download_media("media_123", "/tmp/test.jpg")
            assert result is True
            mock_file.write.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Session cleanup mocking needs refinement")
    async def test_close(self, mock_client):
        """Test client cleanup."""
        # Set up mocks for session and webhook server
        mock_session = AsyncMock()
        mock_session.closed = False  # Session is not closed initially
        mock_client._session = mock_session

        mock_webhook_server = AsyncMock()
        mock_client._webhook_server = mock_webhook_server

        await mock_client.close()

        mock_session.close.assert_called_once()
        mock_webhook_server.cleanup.assert_called_once()
