# 🚀 Praxis Agent - Installation Guide for Beginners

This guide will walk you through installing and setting up Praxis Agent step-by-step, even if you're new to Python or AI tools.

## 📋 What You'll Need

- A computer running **Windows 10 or 11**
- About **30 minutes** of your time
- An internet connection
- (Optional) An API key from OpenRouter, OpenAI, or similar service

## 🔧 Step 1: Install Python

**Why do we need Python?** Praxis Agent is built using Python, so we need it installed on your computer.

1. **Download Python:**
   - Go to [python.org/downloads](https://www.python.org/downloads/)
   - Click the big yellow "Download Python" button
   - This will download the latest Python version

2. **Install Python:**
   - Run the downloaded file
   - **IMPORTANT:** Check the box "Add Python to PATH" at the bottom
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Press `Windows + R`
   - Type `cmd` and press Enter
   - Type `python --version` and press Enter
   - You should see something like "Python 3.11.5"

## 📦 Step 2: Download and Extract Praxis Agent

1. **Download the ZIP file** containing Praxis Agent
2. **Extract the ZIP file:**
   - Right-click the ZIP file
   - Select "Extract All..."
   - Choose a location like `C:\PraxisAgent\` or your Desktop
   - Click "Extract"

## ⚙️ Step 3: Run the Setup

1. **Open the extracted folder**
2. **Double-click `START_PRAXIS.bat`**
   - This will automatically run the setup for you
   - It will install all required components
   - Wait for it to complete (this may take a few minutes)

If the batch file doesn't work:
1. **Open Command Prompt in the folder:**
   - Hold Shift and right-click in the folder
   - Select "Open PowerShell window here" or "Open command window here"
   - Type: `python setup.py`
   - Press Enter

## 🔑 Step 4: Set Up AI Provider (Choose One)

You need an AI service to power Praxis. Here are your options:

### Option A: OpenRouter (Recommended for Beginners)
**Cost: Pay-per-use, starts at $0.001 per request**

1. Go to [openrouter.ai](https://openrouter.ai/)
2. Click "Sign Up" and create an account
3. Go to "Account" → "API Keys"
4. Click "Create Key" and copy the key
5. Open `config\praxis_config.yaml` in Notepad
6. Find the line `api_key: ""`
7. Put your key between the quotes: `api_key: "your-key-here"`
8. Save the file

### Option B: Local AI (Free but requires more setup)
**Cost: Free, but uses your computer's resources**

1. Download [Ollama](https://ollama.ai/)
2. Install it
3. Open Command Prompt
4. Type: `ollama pull llama2:7b`
5. Wait for download to complete
6. Praxis will automatically use this local model

### Option C: OpenAI (More expensive but high quality)
**Cost: More expensive, $0.01-0.03 per request**

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up and add payment method
3. Get API key from "API Keys" section
4. Edit config file as described in Option A

## 🚀 Step 5: Start Praxis Agent

1. **Double-click `START_PRAXIS.bat`**
2. **Look for the Praxis icon in your system tray** (bottom-right corner of screen)
3. **Right-click the icon** to access the menu
4. **Click "Show Control Panel"** to open the main interface

## 🎯 Step 6: Test Your Installation

1. **In the Control Panel, go to the "Tasks" tab**
2. **Type a simple request** like:
   - "What's the weather like today?"
   - "Tell me a fun fact about space"
   - "List the files in my Documents folder"
3. **Click "Submit Task"**
4. **Check the status** - you should see it working!

## 🛠️ Troubleshooting Common Issues

### "Python is not recognized"
- **Problem:** Python wasn't added to PATH during installation
- **Solution:** Reinstall Python and make sure to check "Add Python to PATH"

### "Module not found" errors
- **Problem:** Dependencies not installed
- **Solution:** Run `python setup.py` again

### "API key invalid"
- **Problem:** Wrong API key or format
- **Solution:** Double-check your API key in `config\praxis_config.yaml`

### Agent doesn't respond
- **Problem:** AI service issues
- **Solution:** 
  1. Check your internet connection
  2. Verify API key is correct
  3. Try the local Ollama option instead

### "Permission denied" errors
- **Problem:** Windows security blocking access
- **Solution:** 
  1. Right-click `START_PRAXIS.bat`
  2. Select "Run as administrator"

## 💡 Tips for Beginners

1. **Start Simple:** Begin with basic requests to get familiar with how Praxis works

2. **Check the Logs:** If something goes wrong, look at the "Logs" tab in the Control Panel

3. **Use Local Models:** If you're concerned about costs, set up Ollama for free local AI

4. **Experiment:** Try different types of tasks to see what Praxis can do

5. **Read the README:** The main README.md file has more detailed information

## 🆘 Getting Help

If you're still having trouble:

1. **Check the system tray** - the Praxis icon should be there
2. **Run the diagnostic:** `python praxis.py --check`
3. **Look at the logs** in the `logs` folder
4. **Review this guide** to make sure you didn't miss a step

## 🎉 You're Ready!

Congratulations! You now have Praxis Agent running on your computer. Here are some things to try:

- Ask it to search for information online
- Have it help organize your files
- Request system information
- Ask for help with coding or writing
- Let it automate repetitive tasks

**Remember:** Praxis learns from your interactions, so the more you use it, the better it becomes at helping you!

---

**Need more help?** Check the main README.md file for advanced configuration options and detailed feature explanations.
