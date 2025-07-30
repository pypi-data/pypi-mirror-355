"""
Tests for WhatsApp-Evie configuration.
"""

import pytest
import os
from unittest.mock import patch

from whatsapp_evie.config import ClientConfig, WhatsAppConfig, WebhookConfig, LoggingConfig
from whatsapp_evie.exceptions import ConfigurationError


class TestWhatsAppConfig:
    """Test WhatsAppConfig."""
    
    def test_whatsapp_config_creation(self):
        """Test creating WhatsApp configuration."""
        config = WhatsAppConfig(
            api_key="test_api_key",
            phone_number_id="test_phone_id",
            api_version="v17.0",
            timeout=30,
            max_retries=3
        )
        
        assert config.api_key == "test_api_key"
        assert config.phone_number_id == "test_phone_id"
        assert config.api_version == "v17.0"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.base_url == "https://graph.facebook.com/v17.0"
    
    def test_whatsapp_config_missing_api_key(self):
        """Test WhatsApp configuration with missing API key."""
        with pytest.raises(ConfigurationError):
            WhatsAppConfig(api_key="")
    
    def test_whatsapp_config_defaults(self):
        """Test WhatsApp configuration defaults."""
        config = WhatsAppConfig(api_key="test_api_key")
        
        assert config.api_version == "v17.0"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.rate_limit_requests == 1000
        assert config.rate_limit_window == 3600


class TestWebhookConfig:
    """Test WebhookConfig."""
    
    def test_webhook_config_creation(self):
        """Test creating webhook configuration."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            host="0.0.0.0",
            port=8000,
            path="/webhook",
            verify_token="test_token",
            verify_signature=True
        )
        
        assert config.url == "https://example.com/webhook"
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.path == "/webhook"
        assert config.verify_token == "test_token"
        assert config.verify_signature is True
    
    def test_webhook_config_defaults(self):
        """Test webhook configuration defaults."""
        config = WebhookConfig(test_mode=True)
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.path == "/webhook"
        assert config.verify_signature is True
        assert config.max_payload_size == 1024 * 1024
    
    def test_webhook_config_signature_verification_without_token(self):
        """Test webhook configuration with signature verification but no token."""
        with pytest.raises(ConfigurationError):
            WebhookConfig(verify_signature=True, verify_token=None)


class TestLoggingConfig:
    """Test LoggingConfig."""
    
    def test_logging_config_creation(self):
        """Test creating logging configuration."""
        config = LoggingConfig(
            level="DEBUG",
            format="%(asctime)s - %(message)s",
            file_path="/tmp/test.log",
            max_file_size=5 * 1024 * 1024,
            backup_count=3
        )
        
        assert config.level == "DEBUG"
        assert config.format == "%(asctime)s - %(message)s"
        assert config.file_path == "/tmp/test.log"
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.backup_count == 3
    
    def test_logging_config_defaults(self):
        """Test logging configuration defaults."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert "%(asctime)s" in config.format
        assert config.file_path is None
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5


class TestClientConfig:
    """Test ClientConfig."""
    
    def test_client_config_creation(self):
        """Test creating client configuration."""
        whatsapp_config = WhatsAppConfig(api_key="test_api_key")
        webhook_config = WebhookConfig(test_mode=True)
        
        config = ClientConfig(
            whatsapp=whatsapp_config,
            webhook=webhook_config,
            debug=True
        )
        
        assert config.whatsapp == whatsapp_config
        assert config.webhook == webhook_config
        assert config.debug is True
    
    def test_client_config_from_env(self):
        """Test creating client configuration from environment."""
        env_vars = {
            "WHATSAPP_API_KEY": "test_api_key",
            "WHATSAPP_PHONE_NUMBER_ID": "test_phone_id",
            "WHATSAPP_API_VERSION": "v16.0",
            "WHATSAPP_TIMEOUT": "60",
            "WEBHOOK_URL": "https://example.com/webhook",
            "WEBHOOK_HOST": "127.0.0.1",
            "WEBHOOK_PORT": "9000",
            "WEBHOOK_VERIFY_TOKEN": "test_token",
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = ClientConfig.from_env()
            
            assert config.whatsapp.api_key == "test_api_key"
            assert config.whatsapp.phone_number_id == "test_phone_id"
            assert config.whatsapp.api_version == "v16.0"
            assert config.whatsapp.timeout == 60
            assert config.webhook.url == "https://example.com/webhook"
            assert config.webhook.host == "127.0.0.1"
            assert config.webhook.port == 9000
            assert config.webhook.verify_token == "test_token"
            assert config.logging.level == "DEBUG"
            assert config.debug is True
    
    def test_client_config_from_env_missing_api_key(self):
        """Test creating client configuration from environment with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError):
                ClientConfig.from_env()
    
    def test_client_config_from_dict(self):
        """Test creating client configuration from dictionary."""
        config_dict = {
            "whatsapp": {
                "api_key": "test_api_key",
                "phone_number_id": "test_phone_id"
            },
            "webhook": {
                "url": "https://example.com/webhook",
                "port": 9000,
                "test_mode": True
            },
            "logging": {
                "level": "DEBUG"
            },
            "debug": True
        }
        
        config = ClientConfig.from_dict(config_dict)
        
        assert config.whatsapp.api_key == "test_api_key"
        assert config.whatsapp.phone_number_id == "test_phone_id"
        assert config.webhook.url == "https://example.com/webhook"
        assert config.webhook.port == 9000
        assert config.logging.level == "DEBUG"
        assert config.debug is True
    
    def test_client_config_to_dict(self):
        """Test converting client configuration to dictionary."""
        whatsapp_config = WhatsAppConfig(
            api_key="test_api_key",
            phone_number_id="test_phone_id"
        )
        webhook_config = WebhookConfig(
            url="https://example.com/webhook",
            verify_token="test_token"
        )
        logging_config = LoggingConfig(level="DEBUG")
        
        config = ClientConfig(
            whatsapp=whatsapp_config,
            webhook=webhook_config,
            logging=logging_config,
            debug=True
        )
        
        config_dict = config.to_dict()
        
        # API key should be masked
        assert config_dict["whatsapp"]["api_key"] == "***"
        assert config_dict["whatsapp"]["phone_number_id"] == "test_phone_id"
        assert config_dict["webhook"]["url"] == "https://example.com/webhook"
        # Verify token should be masked
        assert config_dict["webhook"]["verify_token"] == "***"
        assert config_dict["logging"]["level"] == "DEBUG"
        assert config_dict["debug"] is True
