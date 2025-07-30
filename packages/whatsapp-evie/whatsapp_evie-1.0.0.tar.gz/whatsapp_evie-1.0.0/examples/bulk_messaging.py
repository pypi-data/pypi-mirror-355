"""
Bulk messaging example for WhatsApp-Evie integration.

This example demonstrates:
- Sending messages to multiple recipients
- Rate limiting and batch processing
- Progress tracking
- Error handling for bulk operations
"""

import asyncio
import logging
import csv
from typing import List, Dict
from whatsapp_evie import WhatsAppEvieClient, Message, MessageType, ClientConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BulkMessenger:
    """Handle bulk messaging operations."""
    
    def __init__(self, client: WhatsAppEvieClient):
        self.client = client
    
    async def send_bulk_text_messages(self, recipients: List[str], message_text: str) -> Dict[str, bool]:
        """
        Send text messages to multiple recipients.
        
        Args:
            recipients: List of phone numbers
            message_text: Text to send
            
        Returns:
            Dictionary mapping phone numbers to success status
        """
        messages = []
        
        for recipient in recipients:
            message = Message.create_text(
                content=message_text,
                recipient_id=recipient
            )
            messages.append(message)
        
        logger.info(f"Sending {len(messages)} messages...")
        results = await self.client.send_bulk_messages(messages)
        
        # Map results back to phone numbers
        phone_results = {}
        for message, success in results.items():
            # Find the corresponding phone number
            for msg in messages:
                if msg.message_id == message:
                    phone_results[msg.recipient_id] = success
                    break
        
        return phone_results
    
    async def send_personalized_messages(self, recipient_data: List[Dict]) -> Dict[str, bool]:
        """
        Send personalized messages to recipients.
        
        Args:
            recipient_data: List of dictionaries with recipient info
                           Each dict should have 'phone' and other personalization data
            
        Returns:
            Dictionary mapping phone numbers to success status
        """
        messages = []
        
        for data in recipient_data:
            phone = data.get('phone')
            name = data.get('name', 'there')
            
            # Create personalized message
            message_text = f"Hello {name}! This is a personalized message for you."
            
            # Add more personalization based on available data
            if 'product' in data:
                message_text += f"\n\nWe have a special offer on {data['product']} just for you!"
            
            if 'discount' in data:
                message_text += f"\nGet {data['discount']}% off your next purchase!"
            
            message = Message.create_text(
                content=message_text,
                recipient_id=phone
            )
            messages.append(message)
        
        logger.info(f"Sending {len(messages)} personalized messages...")
        results = await self.client.send_bulk_messages(messages)
        
        # Map results back to phone numbers
        phone_results = {}
        for message, success in results.items():
            for msg in messages:
                if msg.message_id == message:
                    phone_results[msg.recipient_id] = success
                    break
        
        return phone_results
    
    async def send_media_to_multiple_recipients(self, recipients: List[str], 
                                              media_url: str, media_type: MessageType,
                                              caption: str = None) -> Dict[str, bool]:
        """
        Send media messages to multiple recipients.
        
        Args:
            recipients: List of phone numbers
            media_url: URL of the media file
            media_type: Type of media (IMAGE, VIDEO, AUDIO, DOCUMENT)
            caption: Optional caption for the media
            
        Returns:
            Dictionary mapping phone numbers to success status
        """
        messages = []
        
        for recipient in recipients:
            message = Message.create_media(
                media_type=media_type,
                url=media_url,
                recipient_id=recipient,
                caption=caption
            )
            messages.append(message)
        
        logger.info(f"Sending {len(messages)} media messages...")
        results = await self.client.send_bulk_messages(messages)
        
        # Map results back to phone numbers
        phone_results = {}
        for message, success in results.items():
            for msg in messages:
                if msg.message_id == message:
                    phone_results[msg.recipient_id] = success
                    break
        
        return phone_results


def load_recipients_from_csv(file_path: str) -> List[Dict]:
    """
    Load recipient data from CSV file.
    
    Expected CSV format:
    phone,name,product,discount
    +1234567890,John Doe,Premium Plan,20
    +0987654321,Jane Smith,Basic Plan,10
    """
    recipients = []
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('phone'):  # Ensure phone number exists
                    recipients.append(row)
        
        logger.info(f"Loaded {len(recipients)} recipients from {file_path}")
        return recipients
        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return []


async def bulk_messaging_example():
    """Example of bulk messaging operations."""
    
    try:
        config = ClientConfig.from_env()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    async with WhatsAppEvieClient(config=config) as client:
        bulk_messenger = BulkMessenger(client)
        
        # Example 1: Simple bulk text message
        logger.info("=== Example 1: Simple Bulk Text Messages ===")
        recipients = [
            "+1234567890",  # Replace with actual phone numbers
            "+0987654321",
            "+1122334455"
        ]
        
        message_text = (
            "🎉 Exciting News! 🎉\n\n"
            "We're launching our new service next week. "
            "Stay tuned for more updates!\n\n"
            "Best regards,\nYour Team"
        )
        
        results = await bulk_messenger.send_bulk_text_messages(recipients, message_text)
        
        # Print results
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        logger.info(f"Bulk messaging results: {successful} successful, {failed} failed")
        for phone, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            logger.info(f"  {phone}: {status}")
        
        # Example 2: Personalized messages from CSV
        logger.info("\n=== Example 2: Personalized Messages ===")
        
        # Create sample CSV data (in real scenario, load from actual file)
        sample_data = [
            {"phone": "+1234567890", "name": "John", "product": "Premium Plan", "discount": "20"},
            {"phone": "+0987654321", "name": "Jane", "product": "Basic Plan", "discount": "10"},
            {"phone": "+1122334455", "name": "Bob", "product": "Enterprise Plan", "discount": "30"}
        ]
        
        # In real scenario, use: sample_data = load_recipients_from_csv("recipients.csv")
        
        results = await bulk_messenger.send_personalized_messages(sample_data)
        
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        logger.info(f"Personalized messaging results: {successful} successful, {failed} failed")
        for phone, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            logger.info(f"  {phone}: {status}")
        
        # Example 3: Bulk media message
        logger.info("\n=== Example 3: Bulk Media Messages ===")
        
        media_url = "https://via.placeholder.com/400x300.png?text=Special+Offer"
        caption = "🎁 Special offer just for you! Check out our latest deals."
        
        results = await bulk_messenger.send_media_to_multiple_recipients(
            recipients=recipients[:2],  # Send to first 2 recipients only
            media_url=media_url,
            media_type=MessageType.IMAGE,
            caption=caption
        )
        
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        logger.info(f"Bulk media messaging results: {successful} successful, {failed} failed")
        for phone, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            logger.info(f"  {phone}: {status}")
        
        logger.info("\n=== Bulk Messaging Example Completed ===")


if __name__ == "__main__":
    asyncio.run(bulk_messaging_example())
