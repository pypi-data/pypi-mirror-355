"""
Example of using the obfuscated WhatsApp-Evie package.

This example demonstrates that the obfuscated package works identically
to the regular package, with the same API and functionality.
"""

import asyncio
import logging

# Import works the same way with obfuscated package
try:
    from whatsapp_evie import WhatsAppEvieClient, Message, MessageType, ClientConfig
    print("✅ Successfully imported obfuscated WhatsApp-Evie package")
except ImportError as e:
    print(f"❌ Failed to import package: {e}")
    print("Make sure you have installed the obfuscated package:")
    print("pip install whatsapp-evie-obfuscated")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_obfuscated_package():
    """Test that the obfuscated package works correctly."""
    
    print("🔒 Testing obfuscated WhatsApp-Evie package...")
    
    try:
        # Test configuration loading
        print("📋 Testing configuration...")
        config = ClientConfig.from_env()
        print("✅ Configuration loaded successfully")
        
        # Test client creation
        print("🤖 Testing client creation...")
        async with WhatsAppEvieClient(config=config) as client:
            print("✅ Client created successfully")
            
            # Test message creation
            print("📝 Testing message creation...")
            message = Message.create_text(
                content="Hello from obfuscated package! 🔒",
                recipient_id="+1234567890"
            )
            print("✅ Message created successfully")
            
            # Test message validation
            print("🔍 Testing message validation...")
            payload = message.to_whatsapp_payload()
            assert payload["type"] == "text"
            assert payload["text"]["body"] == "Hello from obfuscated package! 🔒"
            print("✅ Message validation passed")
            
            # Test handler registration
            print("🎯 Testing handler registration...")
            
            async def test_handler(msg):
                logger.info(f"Handler received: {msg.content}")
            
            client.register_message_handler(MessageType.TEXT, test_handler)
            print("✅ Handler registered successfully")
            
            # Test error handling
            print("⚠️ Testing error handling...")
            try:
                invalid_message = Message.create_text("", "invalid_phone")
            except Exception as e:
                print(f"✅ Error handling works: {type(e).__name__}")
            
        print("🎉 All tests passed! The obfuscated package works correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Detailed error information:")
        return False
    
    return True


def verify_obfuscation():
    """Verify that the code is actually obfuscated."""
    
    print("🔍 Verifying code obfuscation...")
    
    try:
        import inspect
        from whatsapp_evie.client import WhatsAppEvieClient
        
        # Try to get source code
        try:
            source = inspect.getsource(WhatsAppEvieClient)
            
            # Check if source looks obfuscated
            if any(keyword in source for keyword in ["__pyarmor__", "pyarmor_runtime"]):
                print("✅ Code appears to be obfuscated (PyArmor runtime detected)")
                return True
            elif len(source) < 100 or source.count('\n') < 10:
                print("✅ Code appears to be obfuscated (minimal source)")
                return True
            else:
                print("⚠️ Code might not be obfuscated (readable source found)")
                print("This could be the regular package or obfuscation failed")
                return False
                
        except (OSError, TypeError):
            print("✅ Code is obfuscated (source not accessible)")
            return True
            
    except Exception as e:
        print(f"❌ Could not verify obfuscation: {e}")
        return False


def check_package_info():
    """Check package information."""
    
    print("📦 Checking package information...")
    
    try:
        import whatsapp_evie
        
        print(f"Package version: {getattr(whatsapp_evie, '__version__', 'Unknown')}")
        print(f"Package file: {whatsapp_evie.__file__}")
        print(f"Package author: {getattr(whatsapp_evie, '__author__', 'Unknown')}")
        
        # Check if this is the obfuscated version
        package_path = whatsapp_evie.__file__
        if "obfuscated" in package_path.lower():
            print("✅ This appears to be the obfuscated package")
        else:
            print("ℹ️ This might be the regular package")
            
    except Exception as e:
        print(f"❌ Could not get package info: {e}")


async def main():
    """Main function."""
    
    print("🔒 WhatsApp-Evie Obfuscated Package Test")
    print("=" * 50)
    
    # Check package info
    check_package_info()
    print()
    
    # Verify obfuscation
    verify_obfuscation()
    print()
    
    # Test functionality
    success = await test_obfuscated_package()
    print()
    
    if success:
        print("🎉 SUCCESS: Obfuscated package is working correctly!")
        print("The package provides the same functionality as the regular version")
        print("but with enhanced code protection.")
    else:
        print("❌ FAILURE: Obfuscated package has issues")
        print("Please check the installation and configuration.")
    
    print("\n" + "=" * 50)
    print("Test completed.")


if __name__ == "__main__":
    asyncio.run(main())
