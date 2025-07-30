"""
Basic usage example for WhatsApp-Evie integration.

This example demonstrates:
- Setting up the client
- Sending different types of messages
- Handling incoming messages
- Basic error handling
"""

import asyncio
import logging
from whatsapp_evie import WhatsAppEvieClient, Message, MessageType, ClientConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_example():
    """Basic usage example."""
    
    # Method 1: Initialize with environment variables
    # Make sure to set WHATSAPP_API_KEY and other required env vars
    try:
        config = ClientConfig.from_env()
    except Exception as e:
        logger.error(f"Failed to load config from environment: {e}")
        return
    
    # Method 2: Initialize with explicit parameters
    # client = WhatsAppEvieClient(
    #     api_key="your_api_key",
    #     phone_number_id="your_phone_number_id"
    # )
    
    async with WhatsAppEvieClient(config=config) as client:
        
        # Register message handlers
        async def handle_text_message(message: Message):
            logger.info(f"Received text: {message.content} from {message.sender_id}")
            
            # Echo the message back
            response = Message.create_text(
                content=f"Echo: {message.content}",
                recipient_id=message.sender_id
            )
            
            success = await client.send_message(response)
            if success:
                logger.info("Echo sent successfully")
            else:
                logger.error("Failed to send echo")
        
        async def handle_image_message(message: Message):
            logger.info(f"Received image from {message.sender_id}")
            
            # Download the image (optional)
            if message.media_info and message.media_info.media_id:
                success = await client.download_media(
                    message.media_info.media_id,
                    f"/tmp/received_image_{message.message_id}.jpg"
                )
                if success:
                    logger.info("Image downloaded successfully")
        
        # Register handlers
        client.register_message_handler(MessageType.TEXT, handle_text_message)
        client.register_message_handler(MessageType.IMAGE, handle_image_message)
        
        # Send a welcome message
        welcome_message = Message.create_text(
            content="Hello! I'm your WhatsApp bot. Send me a message!",
            recipient_id="+1234567890"  # Replace with actual recipient
        )
        
        try:
            success = await client.send_message(welcome_message)
            if success:
                logger.info("Welcome message sent")
            else:
                logger.error("Failed to send welcome message")
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
        
        # Send an image message
        image_message = Message.create_media(
            media_type=MessageType.IMAGE,
            url="https://via.placeholder.com/300x200.png?text=Hello+World",
            recipient_id="+1234567890",  # Replace with actual recipient
            caption="This is a test image!"
        )
        
        try:
            success = await client.send_message(image_message)
            if success:
                logger.info("Image message sent")
        except Exception as e:
            logger.error(f"Error sending image: {e}")
        
        # Send a location message
        location_message = Message.create_location(
            latitude=37.7749,
            longitude=-122.4194,
            recipient_id="+1234567890",  # Replace with actual recipient
            name="San Francisco",
            address="San Francisco, CA, USA"
        )
        
        try:
            success = await client.send_message(location_message)
            if success:
                logger.info("Location message sent")
        except Exception as e:
            logger.error(f"Error sending location: {e}")
        
        logger.info("Basic example completed. Check your WhatsApp for messages!")


if __name__ == "__main__":
    asyncio.run(basic_example())
