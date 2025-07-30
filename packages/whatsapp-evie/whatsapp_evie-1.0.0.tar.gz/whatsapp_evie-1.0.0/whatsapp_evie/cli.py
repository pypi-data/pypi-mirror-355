"""
Command-line interface for WhatsApp-Evie integration.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .client import WhatsAppEvieClient
from .config import ClientConfig
from .models import Message, MessageType
from .logging_utils import setup_logging, get_logger


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="WhatsApp-Evie Integration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start webhook server
  whatsapp-evie webhook --host 0.0.0.0 --port 8000

  # Send a text message
  whatsapp-evie send-message --to +1234567890 --text "Hello World"

  # Send an image
  whatsapp-evie send-message --to +1234567890 --image https://example.com/image.jpg

  # Validate configuration
  whatsapp-evie validate-config

  # Test webhook endpoint
  whatsapp-evie test-webhook --url https://example.com/webhook
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Webhook command
    webhook_parser = subparsers.add_parser("webhook", help="Start webhook server")
    webhook_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    webhook_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    # Send message command
    send_parser = subparsers.add_parser("send-message", help="Send a message")
    send_parser.add_argument("--to", required=True, help="Recipient phone number")
    send_parser.add_argument("--text", help="Text message content")
    send_parser.add_argument("--image", help="Image URL")
    send_parser.add_argument("--audio", help="Audio URL")
    send_parser.add_argument("--video", help="Video URL")
    send_parser.add_argument("--document", help="Document URL")
    
    # Validate config command
    subparsers.add_parser("validate-config", help="Validate configuration")
    
    # Test webhook command
    test_parser = subparsers.add_parser("test-webhook", help="Test webhook endpoint")
    test_parser.add_argument("--url", required=True, help="Webhook URL to test")
    
    return parser


async def start_webhook(args: argparse.Namespace, config: ClientConfig) -> None:
    """Start webhook server."""
    logger = get_logger("cli.webhook")
    
    try:
        client = WhatsAppEvieClient(config=config)
        
        # Register a simple message handler for demonstration
        async def handle_message(message: Message):
            logger.info(f"Received {message.type} message from {message.sender_id}: {message.content}")
        
        for msg_type in MessageType:
            client.register_message_handler(msg_type, handle_message)
        
        logger.info(f"Starting webhook server on {args.host}:{args.port}")
        await client.start_webhook_server(host=args.host, port=args.port)
        
    except KeyboardInterrupt:
        logger.info("Webhook server stopped")
    except Exception as e:
        logger.error(f"Failed to start webhook server: {e}")
        sys.exit(1)


async def send_message(args: argparse.Namespace, config: ClientConfig) -> None:
    """Send a message."""
    logger = get_logger("cli.send_message")
    
    try:
        client = WhatsAppEvieClient(config=config)
        
        # Determine message type and content
        if args.text:
            message_type = MessageType.TEXT
            content = args.text
        elif args.image:
            message_type = MessageType.IMAGE
            content = args.image
        elif args.audio:
            message_type = MessageType.AUDIO
            content = args.audio
        elif args.video:
            message_type = MessageType.VIDEO
            content = args.video
        elif args.document:
            message_type = MessageType.DOCUMENT
            content = args.document
        else:
            logger.error("No message content provided")
            sys.exit(1)
        
        # Create and send message
        message = Message.create(
            type=message_type,
            content=content,
            recipient_id=args.to
        )
        
        success = await client.send_message(message)
        
        if success:
            logger.info(f"Message sent successfully to {args.to}")
        else:
            logger.error("Failed to send message")
            sys.exit(1)
            
        await client.close()
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        sys.exit(1)


def validate_config(args: argparse.Namespace, config: ClientConfig) -> None:
    """Validate configuration."""
    logger = get_logger("cli.validate_config")
    
    try:
        # Configuration is already validated during creation
        logger.info("Configuration is valid")
        
        # Print configuration (without sensitive data)
        config_dict = config.to_dict()
        print(json.dumps(config_dict, indent=2))
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)


async def test_webhook(args: argparse.Namespace, config: ClientConfig) -> None:
    """Test webhook endpoint."""
    logger = get_logger("cli.test_webhook")
    
    try:
        import aiohttp
        
        # Create test payload
        test_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test_entry_id",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test_phone_id"
                        },
                        "messages": [{
                            "from": "1234567890",
                            "id": "test_message_id",
                            "timestamp": "1234567890",
                            "text": {
                                "body": "Test message"
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(args.url, json=test_payload) as response:
                if response.status == 200:
                    logger.info(f"Webhook test successful: {response.status}")
                else:
                    logger.error(f"Webhook test failed: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text}")
                    sys.exit(1)
                    
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Load configuration
        if args.config and Path(args.config).exists():
            config = ClientConfig.from_env(args.config)
        else:
            config = ClientConfig.from_env()
        
        # Override debug setting if specified
        if args.debug:
            config.debug = True
            config.logging.level = "DEBUG"
        
        # Setup logging
        setup_logging(config.logging)
        
        # Execute command
        if args.command == "webhook":
            asyncio.run(start_webhook(args, config))
        elif args.command == "send-message":
            asyncio.run(send_message(args, config))
        elif args.command == "validate-config":
            validate_config(args, config)
        elif args.command == "test-webhook":
            asyncio.run(test_webhook(args, config))
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
