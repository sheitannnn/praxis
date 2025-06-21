"""
Praxis Agent Setup Script
Handles installation, configuration, and dependency management
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Error: requirements.txt not found")
        return False
    
    try:
        # Try to use pip
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("💡 Try running: pip install -r requirements.txt")
        return False


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "config",
        "data",
        "logs",
        "data/vector_store"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
    
    print("✅ Directories created")


def create_default_config():
    """Create default configuration file"""
    print("⚙️ Creating default configuration...")
    
    config_path = Path("config/praxis_config.yaml")
    
    if config_path.exists():
        print("⚠️ Configuration file already exists, skipping...")
        return True
    
    default_config = """# Praxis Agent Configuration

# Primary LLM Configuration
primary_llm:
  provider: openrouter
  model: openai/gpt-4-turbo-preview
  api_key: ""  # Set your OpenRouter API key here
  base_url: https://openrouter.ai/api/v1
  max_tokens: 4096
  temperature: 0.7
  timeout: 60

# Fallback LLM Configuration (for when primary fails)
fallback_llm:
  provider: ollama
  model: llama2:7b
  base_url: http://localhost:11434
  max_tokens: 4096
  temperature: 0.7
  timeout: 60

# Embedding model for memory system
embedding_model: sentence-transformers/all-MiniLM-L6-v2

# System Configuration
system:
  log_level: INFO
  max_log_files: 10
  log_rotation_mb: 10
  enable_system_tray: true
  auto_start: true
  max_concurrent_tasks: 3
  sandbox_enabled: true

# Security Configuration
security:
  allow_file_operations: true
  allow_network_access: true
  allow_code_execution: true
  restricted_paths:
    - "C:\\Windows\\System32"
    - "C:\\Program Files"
    - "C:\\Users\\*\\AppData\\Roaming\\Microsoft"
  max_file_size_mb: 100

# Directory Paths
data_dir: "./data"
logs_dir: "./logs"
memory_db_path: "./data/memory.db"
vector_db_path: "./data/vector_store"

# Memory Configuration
max_short_term_memories: 100
max_long_term_memories: 10000
memory_retention_days: 30
"""
    
    with open(config_path, 'w') as f:
        f.write(default_config)
    
    print(f"✅ Configuration created: {config_path}")
    return True


def setup_windows_service():
    """Setup Windows-specific features"""
    if os.name != 'nt':
        print("⚠️ Windows-specific setup skipped (not running on Windows)")
        return True
    
    print("🪟 Setting up Windows integration...")
    
    try:
        # Test Windows-specific imports
        import win32api
        import pystray
        print("✅ Windows dependencies available")
        return True
    except ImportError as e:
        print(f"⚠️ Windows dependency missing: {e}")
        print("💡 Some Windows features may not work properly")
        return True


def create_startup_scripts():
    """Create startup scripts"""
    print("📜 Creating startup scripts...")
    
    # Windows batch file
    batch_content = """@echo off
echo Starting Praxis Agent...
cd /d "%~dp0"
python praxis.py --mode gui
pause
"""
    
    with open("start_praxis.bat", 'w') as f:
        f.write(batch_content)
    
    # Python startup script
    python_startup = """#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run main
from praxis import main

if __name__ == "__main__":
    main()
"""
    
    with open("start_praxis.py", 'w') as f:
        f.write(python_startup)
    
    print("✅ Startup scripts created:")
    print("  - start_praxis.bat (Windows)")
    print("  - start_praxis.py (Cross-platform)")


def test_installation():
    """Test if installation is working"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        sys.path.insert(0, str(Path.cwd()))
        
        from config.settings import config_manager
        from gateway.llm_gateway import llm_gateway
        from cognitive.memory_core import memory_core
        from toolkit.actions import action_toolkit
        from core.orchestrator import orchestrator
        
        print("✅ All modules imported successfully")
        
        # Test configuration loading
        config = config_manager.load_config()
        print("✅ Configuration loaded successfully")
        
        # Test memory system
        memory_stats = memory_core.get_memory_stats()
        print("✅ Memory system initialized")
        
        # Test action toolkit
        actions = action_toolkit.get_available_actions()
        print(f"✅ Action toolkit ready ({len(actions)} actions available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_api_key_instructions():
    """Print instructions for setting up API keys"""
    print("""
🔑 API Key Setup Instructions:

To use cloud AI models, you'll need to set up API keys:

1. OpenRouter (Recommended for access to multiple models):
   - Sign up at: https://openrouter.ai/
   - Get your API key from the account dashboard
   - Set it in config/praxis_config.yaml under primary_llm.api_key

2. OpenAI (Alternative):
   - Sign up at: https://platform.openai.com/
   - Get your API key from the API section
   - Update the configuration to use OpenAI provider

3. Local Models (No API key required):
   - Install Ollama from: https://ollama.ai/
   - Pull models: ollama pull llama2:7b
   - The agent can use local models as fallback

Configuration file location: config/praxis_config.yaml

Example configuration:
primary_llm:
  provider: openrouter
  api_key: "your-openrouter-key-here"
""")


def main():
    """Main setup process"""
    print("🚀 Praxis Agent Setup")
    print("=" * 50)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create configuration
    create_default_config()
    
    # Setup Windows features
    setup_windows_service()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Test installation
    if not test_installation():
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your API keys (see instructions below)")
        print("2. Run: python praxis.py --check")
        print("3. Start the agent: python praxis.py")
        print("   Or double-click: start_praxis.bat")
        
        print_api_key_instructions()
    else:
        print("❌ Setup completed with errors")
        print("Please fix the issues above before running the agent")
    
    return success


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
