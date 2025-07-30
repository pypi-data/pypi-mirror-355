"""
Webhook server example for WhatsApp-Evie integration.

This example demonstrates:
- Setting up a webhook server
- Handling different message types
- Implementing a simple chatbot
- Error handling and logging
"""

import asyncio
import logging
from whatsapp_evie import WhatsAppEvieClient, Message, MessageType, ClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleChatBot:
    """A simple chatbot that responds to messages."""
    
    def __init__(self, client: WhatsAppEvieClient):
        self.client = client
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up message handlers."""
        self.client.register_message_handler(MessageType.TEXT, self.handle_text)
        self.client.register_message_handler(MessageType.IMAGE, self.handle_image)
        self.client.register_message_handler(MessageType.LOCATION, self.handle_location)
        self.client.register_message_handler(MessageType.CONTACT, self.handle_contact)
        
        # Register error handler
        self.client.register_error_handler(self.handle_error)
    
    async def handle_text(self, message: Message):
        """Handle text messages."""
        logger.info(f"Received text from {message.sender_id}: {message.content}")
        
        content = message.content.lower().strip()
        response_text = ""
        
        # Simple command processing
        if content in ["hello", "hi", "hey"]:
            response_text = "Hello! How can I help you today?"
        
        elif content in ["help", "/help"]:
            response_text = (
                "Available commands:\n"
                "• hello - Say hello\n"
                "• help - Show this help\n"
                "• time - Get current time\n"
                "• echo <message> - Echo your message\n"
                "• Send me an image and I'll describe it\n"
                "• Send me a location and I'll tell you about it"
            )
        
        elif content == "time":
            import datetime
            now = datetime.datetime.now()
            response_text = f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif content.startswith("echo "):
            echo_text = content[5:]  # Remove "echo " prefix
            response_text = f"You said: {echo_text}"
        
        else:
            response_text = (
                f"I received your message: '{message.content}'\n"
                "Type 'help' to see available commands."
            )
        
        # Send response
        response = Message.create_text(
            content=response_text,
            recipient_id=message.sender_id
        )
        
        try:
            success = await self.client.send_message(response)
            if success:
                logger.info(f"Response sent to {message.sender_id}")
            else:
                logger.error(f"Failed to send response to {message.sender_id}")
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    async def handle_image(self, message: Message):
        """Handle image messages."""
        logger.info(f"Received image from {message.sender_id}")
        
        response_text = "Nice image! 📸"
        
        if message.media_info and message.media_info.caption:
            response_text += f"\nI see you added a caption: '{message.media_info.caption}'"
        
        # Optionally download the image
        if message.media_info and message.media_info.media_id:
            try:
                filename = f"/tmp/received_image_{message.message_id}.jpg"
                success = await self.client.download_media(
                    message.media_info.media_id,
                    filename
                )
                if success:
                    logger.info(f"Image downloaded: {filename}")
                    response_text += "\nI've saved your image for processing."
            except Exception as e:
                logger.error(f"Error downloading image: {e}")
        
        response = Message.create_text(
            content=response_text,
            recipient_id=message.sender_id
        )
        
        await self.client.send_message(response)
    
    async def handle_location(self, message: Message):
        """Handle location messages."""
        logger.info(f"Received location from {message.sender_id}")
        
        if message.location_info:
            lat = message.location_info.latitude
            lon = message.location_info.longitude
            name = message.location_info.name or "Unknown location"
            
            response_text = (
                f"Thanks for sharing your location! 📍\n"
                f"Location: {name}\n"
                f"Coordinates: {lat:.4f}, {lon:.4f}"
            )
            
            if message.location_info.address:
                response_text += f"\nAddress: {message.location_info.address}"
        else:
            response_text = "I received a location, but couldn't parse the details."
        
        response = Message.create_text(
            content=response_text,
            recipient_id=message.sender_id
        )
        
        await self.client.send_message(response)
    
    async def handle_contact(self, message: Message):
        """Handle contact messages."""
        logger.info(f"Received contact from {message.sender_id}")
        
        if message.contact_info:
            name = message.contact_info.name
            response_text = f"Thanks for sharing the contact: {name} 👤"
            
            if message.contact_info.phone:
                response_text += f"\nPhone: {message.contact_info.phone}"
            
            if message.contact_info.email:
                response_text += f"\nEmail: {message.contact_info.email}"
        else:
            response_text = "I received a contact, but couldn't parse the details."
        
        response = Message.create_text(
            content=response_text,
            recipient_id=message.sender_id
        )
        
        await self.client.send_message(response)
    
    async def handle_error(self, error: Exception, message: Message = None):
        """Handle errors."""
        logger.error(f"Error occurred: {error}")
        
        if message:
            error_response = Message.create_text(
                content="Sorry, I encountered an error processing your message. Please try again.",
                recipient_id=message.sender_id
            )
            
            try:
                await self.client.send_message(error_response)
            except Exception as e:
                logger.error(f"Failed to send error response: {e}")


async def main():
    """Main function to run the webhook server."""
    try:
        # Load configuration
        config = ClientConfig.from_env()
        
        # Create client
        async with WhatsAppEvieClient(config=config) as client:
            
            # Create and setup chatbot
            bot = SimpleChatBot(client)
            
            logger.info("Starting WhatsApp webhook server...")
            logger.info(f"Server will run on {config.webhook.host}:{config.webhook.port}")
            logger.info("Make sure your webhook URL is configured in WhatsApp Business API")
            
            # Start the webhook server
            await client.start_webhook_server()
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")


if __name__ == "__main__":
    asyncio.run(main())
