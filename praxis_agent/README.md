# 🤖 Praxis Agent - Your Intelligent AI Assistant

**A next-generation AI agent that runs locally on Windows with support for multiple AI providers including OpenRouter, local models, and more.**

## ✨ Features

- **Multi-AI Provider Support**: Works with OpenRouter, OpenAI, Anthropic, and local models (Ollama)
- **Intelligent Decision Making**: Uses a "Generalized Minimax Strategy" for optimal task execution
- **Memory System**: Learns from past experiences with short-term, long-term, and episodic memory
- **Comprehensive Tool Kit**: File operations, web search, code execution, system monitoring
- **Windows Integration**: System tray interface, background service, easy management
- **Security-First**: Configurable security policies and sandboxed execution
- **User-Friendly**: Both GUI and CLI interfaces available

## 🚀 Quick Start

### Prerequisites

- **Windows 10 or 11** (64-bit)
- **Python 3.8 or higher** ([Download here](https://www.python.org/downloads/))
- **Internet connection** (for cloud AI models)

### Installation

1. **Download and Extract**
   ```bash
   # Extract the zip file to your desired location
   # Navigate to the extracted folder
   cd praxis_agent
   ```

2. **Run Setup**
   ```bash
   python setup.py
   ```
   This will:
   - Install all required dependencies
   - Create necessary directories
   - Generate default configuration
   - Create startup scripts

3. **Configure API Keys** (Choose one or more)

   **Option A: OpenRouter (Recommended)**
   - Sign up at [OpenRouter](https://openrouter.ai/)
   - Get your API key
   - Edit `config/praxis_config.yaml` and add your key:
   ```yaml
   primary_llm:
     api_key: "your-openrouter-key-here"
   ```

   **Option B: Local Models (No API key needed)**
   - Install [Ollama](https://ollama.ai/)
   - Pull a model: `ollama pull llama2:7b`
   - The agent will automatically use local models as fallback

4. **Start the Agent**
   ```bash
   python praxis.py
   ```
   Or double-click `start_praxis.bat`

## 🖥️ Usage

### GUI Mode (Default)

When you start the agent, it runs in the system tray. Look for the Praxis icon in your system tray (bottom-right corner).

**System Tray Menu:**
- **Show Control Panel**: Open the main GUI
- **Quick Task**: Submit a task quickly
- **Status**: View current status
- **Start/Stop Agent**: Control the agent

**Control Panel Features:**
- **Control Tab**: Start/stop agent, view statistics
- **Tasks Tab**: Submit new tasks, view task history
- **Status Tab**: Monitor system resources and memory
- **Logs Tab**: View detailed logs
- **Configuration Tab**: Manage API keys and security settings

### CLI Mode

Run in command-line mode for direct interaction:
```bash
python praxis.py --mode cli
```

**CLI Commands:**
- `help` - Show available commands
- `status` - Display agent status
- `config` - Show configuration
- `config api-key openrouter your-key` - Set API key
- Simply type any request to submit as a task

**Example Tasks:**
```
> Search for the latest Python tutorials
> Create a summary of files in my Documents folder
> Check system performance and memory usage
> Find information about machine learning trends
```

### Task Examples

Praxis can handle a wide variety of tasks:

**Information Gathering:**
- "Find the latest news about artificial intelligence"
- "Search for Python programming tutorials"
- "Look up the weather forecast for this week"

**File Operations:**
- "List all files in my Documents folder"
- "Create a backup of my important files"
- "Read and summarize the contents of report.txt"

**System Management:**
- "Check system performance and memory usage"
- "Monitor CPU usage for the next 5 minutes"
- "List all running processes"

**Code and Automation:**
- "Write a Python script to organize my files"
- "Create a simple web scraper for news headlines"
- "Generate a report from my CSV data"

## ⚙️ Configuration

### Main Configuration File

Edit `config/praxis_config.yaml` to customize the agent:

```yaml
# AI Provider Settings
primary_llm:
  provider: openrouter  # openrouter, openai, anthropic, ollama
  model: openai/gpt-4-turbo-preview
  api_key: "your-api-key-here"

# Security Settings
security:
  allow_file_operations: true
  allow_network_access: true
  allow_code_execution: true
  restricted_paths:
    - "C:\\Windows\\System32"
    - "C:\\Program Files"

# Memory Settings
max_short_term_memories: 100
max_long_term_memories: 10000
memory_retention_days: 30
```

### API Providers

**OpenRouter (Recommended)**
- Access to multiple models (GPT-4, Claude, Llama, etc.)
- Cost-effective pricing
- Sign up: https://openrouter.ai/

**Local Models with Ollama**
- No API costs
- Privacy-focused
- Install: https://ollama.ai/
- Models: `ollama pull llama2:7b`

**OpenAI Direct**
- Official OpenAI API
- High quality but more expensive
- Sign up: https://platform.openai.com/

### Security Configuration

Praxis includes comprehensive security controls:

- **File Operation Restrictions**: Control which directories can be accessed
- **Network Access Control**: Enable/disable internet access
- **Code Execution Sandbox**: Safe execution of generated code
- **Restricted Paths**: Protect system directories

## 🔧 Advanced Usage

### Memory System

Praxis learns from every interaction:

- **Short-term Memory**: Current task context and recent actions
- **Long-term Memory**: Important learnings and successful strategies
- **Episodic Memory**: Complete task execution histories

### Action Toolkit

Available tools include:

**File Operations:**
- `read_file`, `write_file`, `list_directory`
- `copy_file`, `delete_file`

**Web Operations:**
- `search_web`, `fetch_url`
- `extract_text_from_html`

**Code Execution:**
- `execute_python`, `execute_command`

**System Monitoring:**
- `get_system_info`, `get_running_processes`

### Extending Functionality

To add new tools:

1. Create new methods in `toolkit/actions.py`
2. Add to the `actions` dictionary in `ActionToolkit`
3. Update the schema in `get_available_actions()`

## 🐛 Troubleshooting

### Common Issues

**"No module named 'requests'"**
```bash
pip install -r requirements.txt
```

**"Agent not responding"**
1. Check if the agent is running: `python praxis.py --check`
2. View logs in the GUI or `logs/praxis_agent.log`
3. Restart: Stop and start the agent

**"API key invalid"**
1. Verify your API key in `config/praxis_config.yaml`
2. Check the provider settings
3. Test with: `python praxis.py --check`

**"Permission denied" errors**
1. Run as administrator if needed
2. Check security settings in configuration
3. Verify file paths are not restricted

### Getting Help

1. **Check Logs**: GUI → Logs tab or `logs/praxis_agent.log`
2. **Test Setup**: `python praxis.py --check`
3. **View Status**: `python praxis.py --mode cli` then type `status`

### Performance Tips

- **Use Local Models**: For privacy and speed, use Ollama
- **Adjust Memory Settings**: Reduce memory limits if needed
- **Monitor Resources**: Check system performance in GUI
- **Configure Security**: Disable unused features for better performance

## 🔒 Privacy & Security

- **Local Operation**: Agent runs entirely on your machine
- **API Data**: Only task content sent to chosen AI providers
- **No Telemetry**: No usage data collected or transmitted
- **Sandboxed Execution**: Code runs in isolated environment
- **Configurable Restrictions**: Control what the agent can access

## 📝 License

This project is open source. See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional AI providers
- New action tools
- Better Windows integration
- Performance optimizations
- Security enhancements

## 📞 Support

For support and questions:

1. Check this README first
2. Review the troubleshooting section
3. Check the logs for error details
4. Use `python praxis.py --check` to diagnose issues

---

**Praxis Agent - Making AI work for you, locally and intelligently.**
