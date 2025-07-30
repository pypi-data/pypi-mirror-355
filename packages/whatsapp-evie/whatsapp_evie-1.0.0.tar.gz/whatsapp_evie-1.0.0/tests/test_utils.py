"""
Tests for WhatsApp-Evie utilities.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch

from whatsapp_evie.utils import (
    RateLimiter, retry_async, validate_phone_number, sanitize_message_content,
    verify_webhook_signature, format_phone_number, generate_message_id, is_valid_url
)
from whatsapp_evie.exceptions import RateLimitError


class TestRateLimiter:
    """Test RateLimiter."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Should allow 5 requests
        for _ in range(5):
            await limiter.acquire()
        
        assert len(limiter.requests) == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks requests exceeding limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # First 2 requests should succeed
        await limiter.acquire()
        await limiter.acquire()
        
        # Third request should raise RateLimitError
        with pytest.raises(RateLimitError):
            await limiter.acquire()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_window_reset(self):
        """Test rate limiter resets after window expires."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Use up the limit
        await limiter.acquire()
        await limiter.acquire()
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should allow new requests
        await limiter.acquire()
        assert len(limiter.requests) == 1


class TestRetryAsync:
    """Test retry_async decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test retry decorator with successful first attempt."""
        call_count = 0
        
        @retry_async(max_retries=3, delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry decorator with success after failures."""
        call_count = 0
        
        @retry_async(max_retries=3, delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry decorator when all retries are exhausted."""
        call_count = 0
        
        @retry_async(max_retries=2, delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError):
            await test_function()
        
        assert call_count == 3  # Initial attempt + 2 retries


class TestPhoneNumberValidation:
    """Test phone number validation."""
    
    def test_validate_phone_number_valid(self):
        """Test valid phone numbers."""
        valid_numbers = [
            "+1234567890",
            "1234567890",
            "+44 20 7946 0958",
            "+86 138 0013 8000",
            "1-800-555-0199"
        ]
        
        for number in valid_numbers:
            assert validate_phone_number(number), f"Should be valid: {number}"
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone numbers."""
        invalid_numbers = [
            "123",  # Too short
            "123456789012345678",  # Too long
            "abc123",  # Contains letters
            "",  # Empty
            "+",  # Just plus sign
        ]
        
        for number in invalid_numbers:
            assert not validate_phone_number(number), f"Should be invalid: {number}"
    
    def test_format_phone_number(self):
        """Test phone number formatting."""
        test_cases = [
            ("1234567890", "+1234567890"),
            ("+1234567890", "+1234567890"),
            ("1-800-555-0199", "+18005550199"),
            ("+44 20 7946 0958", "+442079460958")
        ]
        
        for input_number, expected in test_cases:
            result = format_phone_number(input_number)
            assert result == expected, f"Expected {expected}, got {result}"


class TestMessageSanitization:
    """Test message content sanitization."""
    
    def test_sanitize_message_content_normal(self):
        """Test sanitizing normal content."""
        content = "Hello, World! 🌍"
        result = sanitize_message_content(content)
        assert result == content
    
    def test_sanitize_message_content_control_chars(self):
        """Test sanitizing content with control characters."""
        content = "Hello\x00World\x01!"
        result = sanitize_message_content(content)
        assert result == "HelloWorld!"
    
    def test_sanitize_message_content_preserve_whitespace(self):
        """Test sanitizing content preserves valid whitespace."""
        content = "Hello\nWorld\tTest\r\n"
        result = sanitize_message_content(content)
        assert result == content
    
    def test_sanitize_message_content_truncate(self):
        """Test sanitizing content truncates long messages."""
        content = "A" * 5000
        result = sanitize_message_content(content, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")
    
    def test_sanitize_message_content_empty(self):
        """Test sanitizing empty content."""
        result = sanitize_message_content("")
        assert result == ""
        
        result = sanitize_message_content(None)
        assert result == ""


class TestWebhookSignatureVerification:
    """Test webhook signature verification."""
    
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature."""
        payload = b'{"test": "data"}'
        secret = "test_secret"
        
        import hmac
        import hashlib
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert verify_webhook_signature(payload, signature, secret)
        assert verify_webhook_signature(payload, f"sha256={signature}", secret)
    
    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature."""
        payload = b'{"test": "data"}'
        secret = "test_secret"
        wrong_signature = "invalid_signature"
        
        assert not verify_webhook_signature(payload, wrong_signature, secret)
    
    def test_verify_webhook_signature_missing_params(self):
        """Test webhook signature verification with missing parameters."""
        payload = b'{"test": "data"}'
        
        assert not verify_webhook_signature(payload, "", "secret")
        assert not verify_webhook_signature(payload, "signature", "")
        assert not verify_webhook_signature(payload, None, "secret")
        assert not verify_webhook_signature(payload, "signature", None)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_generate_message_id(self):
        """Test message ID generation."""
        id1 = generate_message_id()
        id2 = generate_message_id()
        
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0
    
    def test_is_valid_url(self):
        """Test URL validation."""
        valid_urls = [
            "https://example.com",
            "http://example.com/path",
            "https://subdomain.example.com/path?query=value",
            "ftp://files.example.com/file.txt"
        ]
        
        invalid_urls = [
            "not_a_url",
            "http://",
            "://example.com",
            "",
            "example.com"  # Missing scheme
        ]
        
        for url in valid_urls:
            assert is_valid_url(url), f"Should be valid: {url}"
        
        for url in invalid_urls:
            assert not is_valid_url(url), f"Should be invalid: {url}"
