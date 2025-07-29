#!/usr/bin/env python3
"""
Simple test script to verify the package imports work correctly.
"""

def test_imports():
    """Test that all main components can be imported."""
    try:
        from velaris_csm_access_kit import (
            TTLCache,
            get_secret,
            ServiceRegistry,
            AsyncMultiDbConnectionPool,
            validate_token,
            TokenService,
            AuthenticatedService,
            UserManagmentService,
            TOKEN_SERVICE_PARAMETER
        )
        print("✅ All imports successful!")
        
        # Test basic functionality
        cache = TTLCache(ttl=60)
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        assert value == "test_value", "Cache test failed"
        print("✅ TTLCache basic functionality works!")
        
        print("✅ Package is ready for use!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
