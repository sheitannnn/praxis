# 🔧 Praxis Agent - Troubleshooting Guide

This guide helps you diagnose and fix common issues with Praxis Agent.

## 🚨 Quick Diagnostic

**First, run the built-in diagnostic:**
```bash
python praxis.py --check
```

This will check your configuration, dependencies, and API connectivity.

---

## 📋 Common Issues and Solutions

### 🐍 Python Issues

#### "Python is not recognized as an internal or external command"
**Cause:** Python not installed or not in PATH

**Solutions:**
1. **Reinstall Python:**
   - Download from [python.org](https://python.org/downloads/)
   - **IMPORTANT:** Check "Add Python to PATH" during installation
   - Restart your computer after installation

2. **Manually add Python to PATH:**
   - Find your Python installation (usually `C:\Python311\` or `C:\Users\[username]\AppData\Local\Programs\Python\`)
   - Add this path to your Windows PATH environment variable

#### "ModuleNotFoundError: No module named..."
**Cause:** Missing dependencies

**Solutions:**
1. **Run setup again:**
   ```bash
   python setup.py
   ```

2. **Manual installation:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Update pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

### 🔑 API and Configuration Issues

#### "Invalid API key" or "Authentication failed"
**Cause:** Wrong or missing API key

**Solutions:**
1. **Check your API key:**
   - Open `config\praxis_config.yaml`
   - Verify the API key is correctly entered
   - Make sure there are no extra spaces or characters

2. **Test your API key:**
   - For OpenRouter: Visit [openrouter.ai](https://openrouter.ai/) and check your account
   - For OpenAI: Visit [platform.openai.com](https://platform.openai.com/) and verify your key

3. **Use CLI to set API key:**
   ```bash
   python praxis.py --mode cli
   > config api-key openrouter your-key-here
   ```

#### "Configuration file not found"
**Cause:** Missing configuration file

**Solutions:**
1. **Run setup:**
   ```bash
   python setup.py
   ```

2. **Manual creation:**
   - Copy `config\example_config.yaml` to `config\praxis_config.yaml`
   - Edit the new file with your settings

### 🌐 Network and Connectivity Issues

#### "Connection timeout" or "Network error"
**Cause:** Network connectivity problems

**Solutions:**
1. **Check internet connection:**
   - Try browsing to any website
   - Test: `ping google.com` in Command Prompt

2. **Check firewall/antivirus:**
   - Temporarily disable firewall/antivirus
   - Add Python to firewall exceptions

3. **Use local models:**
   - Install [Ollama](https://ollama.ai/)
   - Run: `ollama pull llama2:7b`
   - Update config to use local models

#### "SSL Certificate verification failed"
**Cause:** Corporate firewall or outdated certificates

**Solutions:**
1. **Update certificates:**
   ```bash
   pip install --upgrade certifi
   ```

2. **Corporate network workaround:**
   - Contact your IT department
   - They may need to whitelist AI service domains

### 💾 Memory and Performance Issues

#### Agent runs slowly or freezes
**Cause:** Insufficient resources or configuration issues

**Solutions:**
1. **Check system resources:**
   - Close unnecessary programs
   - Monitor RAM usage in Task Manager

2. **Adjust configuration:**
   - Reduce `max_concurrent_tasks` in config
   - Lower `max_short_term_memories`
   - Disable unused features

3. **Use lighter models:**
   - Switch to smaller local models
   - Use less resource-intensive AI providers

#### "Out of memory" errors
**Cause:** Vector database or memory system issues

**Solutions:**
1. **Clear memory database:**
   - Stop the agent
   - Delete `data\vector_store` folder
   - Restart the agent

2. **Reduce memory limits:**
   ```yaml
   max_short_term_memories: 50
   max_long_term_memories: 5000
   ```

### 🖥️ Windows Integration Issues

#### System tray icon doesn't appear
**Cause:** Windows display issues or permissions

**Solutions:**
1. **Check system tray settings:**
   - Right-click taskbar → "Taskbar settings"
   - Ensure system tray icons are enabled

2. **Run as administrator:**
   - Right-click `START_PRAXIS.bat`
   - Select "Run as administrator"

3. **Use CLI mode:**
   ```bash
   python praxis.py --mode cli
   ```

#### GUI doesn't open or crashes
**Cause:** Display driver or tkinter issues

**Solutions:**
1. **Update display drivers**

2. **Try CLI mode:**
   ```bash
   python praxis.py --mode cli
   ```

3. **Check tkinter installation:**
   ```bash
   python -c "import tkinter; print('tkinter works')"
   ```

### 🔒 Security and Permissions Issues

#### "Permission denied" file errors
**Cause:** Windows file permissions

**Solutions:**
1. **Run as administrator:**
   - Right-click Command Prompt
   - Select "Run as administrator"
   - Navigate to Praxis folder and run

2. **Check file permissions:**
   - Right-click Praxis folder
   - Properties → Security
   - Ensure your user has full control

3. **Move to user directory:**
   - Copy Praxis to `C:\Users\[username]\Documents\PraxisAgent\`

#### Code execution blocked
**Cause:** Security software interference

**Solutions:**
1. **Check antivirus settings:**
   - Add Praxis folder to antivirus exceptions
   - Temporarily disable real-time protection for testing

2. **Update security configuration:**
   ```yaml
   security:
     allow_code_execution: false  # Disable if not needed
   ```

---

## 🔍 Advanced Diagnostics

### Log Analysis

**Check the logs for detailed error information:**
1. **Open log folder:** `logs\`
2. **View latest log:** `praxis_agent.log`
3. **Look for ERROR or WARNING messages**

**Common log patterns:**
- `ConnectionError`: Network/API issues
- `ModuleNotFoundError`: Missing dependencies
- `PermissionError`: File/folder access issues
- `ConfigurationError`: Invalid configuration

### Manual Testing

**Test individual components:**

1. **Test configuration:**
   ```python
   from config.settings import config_manager
   config = config_manager.load_config()
   print("Config loaded successfully")
   ```

2. **Test LLM gateway:**
   ```python
   import asyncio
   from gateway.llm_gateway import llm_gateway
   
   async def test():
       response = await llm_gateway.generate("Hello, how are you?")
       print(response.content)
   
   asyncio.run(test())
   ```

3. **Test memory system:**
   ```python
   from cognitive.memory_core import memory_core
   stats = memory_core.get_memory_stats()
   print(stats)
   ```

### Environment Information

**Gather system information for support:**
```bash
python praxis.py --check > system_info.txt
```

This creates a file with:
- Python version and installation
- Installed packages
- Configuration status
- System resources
- Error details

---

## 📞 Getting Further Help

### Before Asking for Help

1. **Run the diagnostic:** `python praxis.py --check`
2. **Check the logs:** Look in `logs\praxis_agent.log`
3. **Try safe mode:** Run with minimal configuration
4. **Document the error:** Copy exact error messages

### Information to Include

When reporting issues, include:
- **Python version:** `python --version`
- **Windows version:** Windows 10/11
- **Error messages:** Exact text from errors
- **Configuration:** Your `praxis_config.yaml` (remove API keys)
- **Logs:** Recent entries from log files
- **Steps to reproduce:** What you were doing when it failed

### Safe Mode

To run in safe mode with minimal features:
1. **Copy `config\example_config.yaml` to `config\safe_config.yaml`**
2. **Edit safe config:**
   ```yaml
   security:
     allow_file_operations: false
     allow_network_access: true
     allow_code_execution: false
   ```
3. **Start with safe config:**
   ```bash
   python praxis.py --config config\safe_config.yaml
   ```

---

## ✅ Prevention Tips

1. **Regular updates:** Keep Python and packages updated
2. **Backup configuration:** Save working `praxis_config.yaml`
3. **Monitor resources:** Check system performance regularly
4. **Test changes:** Run `--check` after configuration changes
5. **Read logs:** Review logs periodically for warnings

---

**Remember:** Most issues are related to configuration, API keys, or Python environment. The diagnostic tool (`python praxis.py --check`) can identify and often fix common problems automatically.
