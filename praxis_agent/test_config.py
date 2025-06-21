#!/usr/bin/env python3
"""
Test script to verify configuration loading works correctly
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_config():
    """Test configuration loading"""
    try:
        print("🔧 Testing configuration loading...")
        
        # Import configuration
        from config.settings import config_manager
        
        print("✅ Configuration module imported successfully")
        
        # Load configuration
        config = config_manager.load_config()
        
        print("✅ Configuration loaded successfully")
        print(f"   Primary provider: {config.primary_llm.provider}")
        print(f"   Primary model: {config.primary_llm.model}")
        print(f"   Fallback provider: {config.fallback_llm.provider if config.fallback_llm else 'None'}")
        print(f"   Log level: {config.system.log_level}")
        
        # Validate configuration
        issues = config_manager.validate_config()
        
        if issues:
            print("⚠️ Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
