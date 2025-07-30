WhatsApp-Evie Integration Library
==================================

A professional Python library that provides a comprehensive interface to integrate 
WhatsApp messaging with Evie, featuring advanced message handling, webhook support,
rate limiting, retry logic, and extensive customization options.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   configuration
   api_reference
   examples
   contributing
   changelog

Features
--------

* **Comprehensive Message Support**: Send and receive text, images, audio, video, documents, locations, and contacts
* **Advanced Webhook Server**: Built-in webhook server with signature verification and health checks
* **Rate Limiting**: Intelligent rate limiting to respect WhatsApp API limits
* **Retry Logic**: Automatic retry with exponential backoff for failed requests
* **Type Safety**: Full type hints and Pydantic models for data validation
* **Async/Await Support**: Built for modern async Python applications
* **Error Handling**: Comprehensive error handling with custom exceptions
* **Logging**: Structured logging with configurable levels and outputs
* **CLI Interface**: Command-line interface for testing and automation
* **Bulk Operations**: Efficient bulk messaging with progress tracking

Quick Start
-----------

Installation::

    pip install whatsapp-evie

Basic usage:

.. code-block:: python

    import asyncio
    from whatsapp_evie import WhatsAppEvieClient, Message, MessageType

    async def main():
        # Initialize client
        client = WhatsAppEvieClient(
            api_key="your_api_key",
            phone_number_id="your_phone_number_id"
        )
        
        # Send a message
        message = Message.create_text(
            content="Hello from WhatsApp-Evie!",
            recipient_id="+1234567890"
        )
        
        async with client:
            success = await client.send_message(message)
            print(f"Message sent: {success}")

    asyncio.run(main())

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
