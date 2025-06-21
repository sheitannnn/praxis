"""
Praxis Agent - Main Entry Point
A next-generation AI agent for Windows with local and cloud AI capabilities
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import config_manager
from core.orchestrator import orchestrator
from integration.windows_service import main as run_gui


def setup_logging():
    """Setup logging configuration"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    config = config_manager.load_config()
    
    # Ensure logs directory exists
    Path(config.logs_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.system.log_level))
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        Path(config.logs_dir) / "praxis_agent.log",
        maxBytes=config.system.log_rotation_mb * 1024 * 1024,
        backupCount=config.system.max_log_files
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    logger.addHandler(console_handler)
    
    return logger


async def run_cli_mode():
    """Run in CLI mode for direct interaction"""
    print("🤖 Praxis Agent - CLI Mode")
    print("Type 'help' for commands, 'quit' to exit")
    print("-" * 50)
    
    # Start orchestrator
    orchestrator_task = asyncio.create_task(orchestrator.start())
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print_help()
                elif user_input.lower() == 'status':
                    print_status()
                elif user_input.lower() == 'config':
                    print_config()
                elif user_input.lower().startswith('config '):
                    handle_config_command(user_input)
                else:
                    # Submit as task
                    print(f"📋 Submitting task: {user_input}")
                    task = await orchestrator.execute_goal(user_input)
                    print(f"✅ Task submitted with ID: {task.id}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        # Stop orchestrator
        await orchestrator.stop()
        if not orchestrator_task.done():
            orchestrator_task.cancel()


def print_help():
    """Print CLI help"""
    help_text = """
📖 Praxis Agent Commands:

Basic Commands:
  help              - Show this help message
  status            - Show agent status
  config            - Show current configuration
  quit/exit/q       - Exit the agent

Configuration:
  config show       - Show detailed configuration
  config set <key> <value> - Set configuration value
  config api-key <provider> <key> - Set API key

Task Submission:
  Simply type any natural language request to submit it as a task.
  
Examples:
  - Search for the latest news about AI
  - Create a summary of my recent documents
  - Check system performance
  - Find Python tutorials online

The agent will automatically plan and execute the task using available tools.
"""
    print(help_text)


def print_status():
    """Print current status"""
    try:
        status = orchestrator.get_status()
        print(f"""
📊 Agent Status:
  Running: {"Yes" if status['is_running'] else "No"}
  Active Tasks: {status['active_tasks']}
  Queued Tasks: {status['queued_tasks']}
  
Memory Stats:
  Short-term: {status['memory_stats'].get('short_term_count', 0)}
  Long-term: {status['memory_stats'].get('long_term_count', 0)}
  Episodes: {status['memory_stats'].get('episodic_count', 0)}
  Success Rate: {status['memory_stats'].get('success_rate', 0.0):.1%}

LLM Usage:
  Total Tokens: {status['llm_usage']['tokens']['total']}
  Session Tokens: {status['llm_usage']['tokens']['session']}
  Primary Model: {status['llm_usage']['primary_model']}
""")
    except Exception as e:
        print(f"❌ Error getting status: {e}")


def print_config():
    """Print current configuration"""
    try:
        config = config_manager.load_config()
        print(f"""
⚙️ Configuration:
  Primary LLM: {config.primary_llm.provider} - {config.primary_llm.model}
  Fallback LLM: {config.fallback_llm.provider if config.fallback_llm else 'None'} - {config.fallback_llm.model if config.fallback_llm else 'None'}
  
  Security:
    File Operations: {"Enabled" if config.security.allow_file_operations else "Disabled"}
    Network Access: {"Enabled" if config.security.allow_network_access else "Disabled"}
    Code Execution: {"Enabled" if config.security.allow_code_execution else "Disabled"}
  
  Paths:
    Data Directory: {config.data_dir}
    Logs Directory: {config.logs_dir}
    Memory DB: {config.memory_db_path}
""")
    except Exception as e:
        print(f"❌ Error getting configuration: {e}")


def handle_config_command(command):
    """Handle configuration commands"""
    parts = command.split()
    
    if len(parts) < 2:
        print("❌ Invalid config command. Use 'help' for usage.")
        return
    
    subcommand = parts[1].lower()
    
    if subcommand == "show":
        print_config()
    elif subcommand == "api-key" and len(parts) >= 4:
        provider = parts[2].lower()
        api_key = parts[3]
        try:
            from config.settings import AIProvider
            if provider in [p.value for p in AIProvider]:
                config_manager.update_api_key(AIProvider(provider), api_key)
                print(f"✅ API key updated for {provider}")
            else:
                print(f"❌ Unknown provider: {provider}")
        except Exception as e:
            print(f"❌ Error updating API key: {e}")
    else:
        print("❌ Unknown config command. Use 'help' for usage.")


def check_setup():
    """Check if the agent is properly set up"""
    issues = []
    
    try:
        # Check configuration
        config_issues = config_manager.validate_config()
        issues.extend(config_issues)
        
        # Check dependencies
        try:
            import requests
            import pystray
            import chromadb
            import sentence_transformers
        except ImportError as e:
            issues.append(f"Missing dependency: {e}")
        
        if issues:
            print("⚠️ Setup Issues Found:")
            for issue in issues:
                print(f"  - {issue}")
            print("\n📖 Please run 'python setup.py' to fix these issues.")
            return False
        else:
            print("✅ Praxis Agent is properly configured!")
            return True
            
    except Exception as e:
        print(f"❌ Error during setup check: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Praxis Agent - AI Assistant")
    parser.add_argument("--mode", choices=["gui", "cli"], default="gui",
                       help="Run in GUI or CLI mode (default: gui)")
    parser.add_argument("--check", action="store_true",
                       help="Check setup and configuration")
    parser.add_argument("--version", action="version", version="Praxis Agent 1.0")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Praxis Agent...")
    
    try:
        # Check setup if requested
        if args.check:
            check_setup()
            return
        
        # Validate setup before running
        if not check_setup():
            print("\n❌ Cannot start agent due to configuration issues.")
            print("Run with --check to see detailed issues.")
            return
        
        # Run in selected mode
        if args.mode == "cli":
            print("🖥️ Starting CLI mode...")
            asyncio.run(run_cli_mode())
        else:
            print("🖼️ Starting GUI mode...")
            run_gui()
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
