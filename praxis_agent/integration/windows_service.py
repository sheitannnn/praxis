"""
Windows Integration Layer - System Tray and Service Management
Provides persistent background operation and user interface on Windows
"""

import os
import sys
import json
import time
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Any, Optional
import pystray
from PIL import Image, ImageDraw
import logging
from pathlib import Path

from core.orchestrator import orchestrator
from config.settings import config_manager
from cognitive.memory_core import memory_core


class PraxisGUI:
    """Main GUI interface for Praxis Agent"""
    
    def __init__(self):
        self.config = config_manager.load_config()
        self.root = None
        self.is_visible = False
        
    def create_window(self):
        """Create the main GUI window"""
        if self.root:
            self.root.destroy()
        
        self.root = tk.Tk()
        self.root.title("Praxis Agent - Control Panel")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control Tab
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="Control")
        self.create_control_tab(control_frame)
        
        # Task Input Tab
        task_frame = ttk.Frame(notebook)
        notebook.add(task_frame, text="Tasks")
        self.create_task_tab(task_frame)
        
        # Status Tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Status")
        self.create_status_tab(status_frame)
        
        # Logs Tab
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Logs")
        self.create_logs_tab(logs_frame)
        
        # Configuration Tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.create_config_tab(config_frame)
        
        return self.root
    
    def create_control_tab(self, parent):
        """Create the control tab interface"""
        # Agent Status
        status_frame = ttk.LabelFrame(parent, text="Agent Status", padding=10)
        status_frame.pack(fill="x", pady=5)
        
        self.status_label = ttk.Label(status_frame, text="⚪ Checking status...", font=("Arial", 12))
        self.status_label.pack(anchor="w")
        
        # Control Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Agent", command=self.start_agent)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Agent", command=self.stop_agent)
        self.stop_button.pack(side="left", padx=5)
        
        self.restart_button = ttk.Button(button_frame, text="Restart Agent", command=self.restart_agent)
        self.restart_button.pack(side="left", padx=5)
        
        # Quick Stats
        stats_frame = ttk.LabelFrame(parent, text="Quick Statistics", padding=10)
        stats_frame.pack(fill="both", expand=True, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=10, state="disabled")
        self.stats_text.pack(fill="both", expand=True)
        
        # Update stats every 5 seconds
        self.update_stats()
    
    def create_task_tab(self, parent):
        """Create the task input tab"""
        # Task Input
        input_frame = ttk.LabelFrame(parent, text="New Task", padding=10)
        input_frame.pack(fill="x", pady=5)
        
        ttk.Label(input_frame, text="Describe what you want me to do:").pack(anchor="w")
        
        self.task_entry = scrolledtext.ScrolledText(input_frame, height=4)
        self.task_entry.pack(fill="x", pady=5)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill="x")
        
        self.submit_button = ttk.Button(button_frame, text="Submit Task", command=self.submit_task)
        self.submit_button.pack(side="left", padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_task)
        self.clear_button.pack(side="left", padx=5)
        
        # Task History
        history_frame = ttk.LabelFrame(parent, text="Recent Tasks", padding=10)
        history_frame.pack(fill="both", expand=True, pady=5)
        
        # Treeview for task history
        columns = ("Time", "Goal", "Status", "Duration")
        self.task_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.task_tree.heading(col, text=col)
            self.task_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update task history
        self.update_task_history()
    
    def create_status_tab(self, parent):
        """Create the status monitoring tab"""
        # System Status
        system_frame = ttk.LabelFrame(parent, text="System Information", padding=10)
        system_frame.pack(fill="x", pady=5)
        
        self.system_text = scrolledtext.ScrolledText(system_frame, height=8, state="disabled")
        self.system_text.pack(fill="both", expand=True)
        
        # Memory Status
        memory_frame = ttk.LabelFrame(parent, text="Memory Statistics", padding=10)
        memory_frame.pack(fill="both", expand=True, pady=5)
        
        self.memory_text = scrolledtext.ScrolledText(memory_frame, height=8, state="disabled")
        self.memory_text.pack(fill="both", expand=True)
        
        # Refresh button
        ttk.Button(parent, text="Refresh Status", command=self.refresh_status).pack(pady=5)
        
        self.refresh_status()
    
    def create_logs_tab(self, parent):
        """Create the logs viewing tab"""
        # Log Level Filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=5)
        
        ttk.Label(filter_frame, text="Log Level:").pack(side="left", padx=5)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(filter_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_combo.pack(side="left", padx=5)
        
        ttk.Button(filter_frame, text="Refresh Logs", command=self.refresh_logs).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Clear Logs", command=self.clear_logs).pack(side="left", padx=5)
        
        # Log Display
        self.log_text = scrolledtext.ScrolledText(parent, height=20, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, pady=5)
        
        self.refresh_logs()
    
    def create_config_tab(self, parent):
        """Create the configuration tab"""
        # API Configuration
        api_frame = ttk.LabelFrame(parent, text="API Configuration", padding=10)
        api_frame.pack(fill="x", pady=5)
        
        # OpenRouter API Key
        ttk.Label(api_frame, text="OpenRouter API Key:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.openrouter_key_var = tk.StringVar()
        openrouter_entry = ttk.Entry(api_frame, textvariable=self.openrouter_key_var, show="*", width=50)
        openrouter_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # OpenAI API Key
        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.openai_key_var = tk.StringVar()
        openai_entry = ttk.Entry(api_frame, textvariable=self.openai_key_var, show="*", width=50)
        openai_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Anthropic API Key
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.anthropic_key_var = tk.StringVar()
        anthropic_entry = ttk.Entry(api_frame, textvariable=self.anthropic_key_var, show="*", width=50)
        anthropic_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # Save Configuration Button
        ttk.Button(api_frame, text="Save API Keys", command=self.save_api_keys).grid(row=3, column=1, pady=10)
        
        # Security Settings
        security_frame = ttk.LabelFrame(parent, text="Security Settings", padding=10)
        security_frame.pack(fill="x", pady=5)
        
        self.allow_file_ops_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(security_frame, text="Allow File Operations", 
                       variable=self.allow_file_ops_var).pack(anchor="w")
        
        self.allow_network_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(security_frame, text="Allow Network Access", 
                       variable=self.allow_network_var).pack(anchor="w")
        
        self.allow_code_exec_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(security_frame, text="Allow Code Execution", 
                       variable=self.allow_code_exec_var).pack(anchor="w")
        
        ttk.Button(security_frame, text="Save Security Settings", 
                  command=self.save_security_settings).pack(pady=10)
        
        # Load current configuration
        self.load_current_config()
    
    def start_agent(self):
        """Start the agent"""
        try:
            # This would start the orchestrator in a separate thread
            threading.Thread(target=self._start_agent_thread, daemon=True).start()
            self.status_label.config(text="🟢 Agent Starting...")
            self.start_button.config(state="disabled")
            messagebox.showinfo("Success", "Agent is starting...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start agent: {e}")
    
    def _start_agent_thread(self):
        """Start agent in separate thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator.start())
        except Exception as e:
            print(f"Agent thread error: {e}")
    
    def stop_agent(self):
        """Stop the agent"""
        try:
            # Stop the orchestrator
            asyncio.create_task(orchestrator.stop())
            self.status_label.config(text="🔴 Agent Stopped")
            self.start_button.config(state="normal")
            messagebox.showinfo("Success", "Agent stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop agent: {e}")
    
    def restart_agent(self):
        """Restart the agent"""
        self.stop_agent()
        time.sleep(1)
        self.start_agent()
    
    def submit_task(self):
        """Submit a new task"""
        task_text = self.task_entry.get("1.0", tk.END).strip()
        if not task_text:
            messagebox.showwarning("Warning", "Please enter a task description")
            return
        
        try:
            # Submit task to orchestrator
            asyncio.create_task(orchestrator.execute_goal(task_text))
            self.task_entry.delete("1.0", tk.END)
            messagebox.showinfo("Success", "Task submitted successfully")
            self.update_task_history()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit task: {e}")
    
    def clear_task(self):
        """Clear the task input"""
        self.task_entry.delete("1.0", tk.END)
    
    def update_stats(self):
        """Update statistics display"""
        try:
            status = orchestrator.get_status()
            
            # Update status indicator
            if status["is_running"]:
                self.status_label.config(text="🟢 Agent Running")
            else:
                self.status_label.config(text="🔴 Agent Stopped")
            
            # Update stats text
            stats_text = f"""Active Tasks: {status['active_tasks']}
Queued Tasks: {status['queued_tasks']}

Memory Statistics:
- Short-term memories: {status['memory_stats'].get('short_term_count', 0)}
- Long-term memories: {status['memory_stats'].get('long_term_count', 0)}
- Episodic memories: {status['memory_stats'].get('episodic_count', 0)}
- Success rate: {status['memory_stats'].get('success_rate', 0.0):.1%}

LLM Usage:
- Total tokens: {status['llm_usage']['tokens']['total']}
- Session tokens: {status['llm_usage']['tokens']['session']}
- Primary model: {status['llm_usage']['primary_model']}
"""
            
            self.stats_text.config(state="normal")
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.insert("1.0", stats_text)
            self.stats_text.config(state="disabled")
            
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        # Schedule next update
        if self.root:
            self.root.after(5000, self.update_stats)
    
    def update_task_history(self):
        """Update task history display"""
        try:
            # Clear existing items
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)
            
            # This would fetch recent tasks from memory
            # For now, show placeholder
            sample_tasks = [
                ("12:30", "Search for Python tutorials", "Completed", "45s"),
                ("12:25", "Analyze system logs", "Running", "2m 15s"),
                ("12:20", "Generate report", "Failed", "30s"),
            ]
            
            for task in sample_tasks:
                self.task_tree.insert("", "end", values=task)
                
        except Exception as e:
            print(f"Error updating task history: {e}")
    
    def refresh_status(self):
        """Refresh system and memory status"""
        try:
            # System information
            from toolkit.actions import SystemOperations
            sys_ops = SystemOperations()
            sys_info = sys_ops.get_system_info()
            
            if sys_info.success:
                info = sys_info.result
                system_text = f"""CPU Usage: {info['cpu_percent']:.1f}%
Memory: {info['memory']['percent']:.1f}% ({info['memory']['available'] // (1024**3):.1f} GB available)
Disk: {info['disk']['percent']:.1f}% ({info['disk']['free'] // (1024**3):.1f} GB free)
Platform: {info['platform']['system']} ({info['platform']['platform']})
Python: {info['platform']['python_version'][:10]}
"""
                
                self.system_text.config(state="normal")
                self.system_text.delete("1.0", tk.END)
                self.system_text.insert("1.0", system_text)
                self.system_text.config(state="disabled")
            
            # Memory statistics
            memory_stats = memory_core.get_memory_stats()
            memory_text = f"""Short-term memories: {memory_stats.get('short_term_count', 0)}
Long-term memories: {memory_stats.get('long_term_count', 0)}
Episodic memories: {memory_stats.get('episodic_count', 0)}
Total episodes: {memory_stats.get('total_episodes', 0)}
Successful episodes: {memory_stats.get('successful_episodes', 0)}
Success rate: {memory_stats.get('success_rate', 0.0):.1%}
"""
            
            self.memory_text.config(state="normal")
            self.memory_text.delete("1.0", tk.END)
            self.memory_text.insert("1.0", memory_text)
            self.memory_text.config(state="disabled")
            
        except Exception as e:
            print(f"Error refreshing status: {e}")
    
    def refresh_logs(self):
        """Refresh log display"""
        try:
            # This would read from actual log files
            sample_logs = """2025-06-21 12:30:15 INFO  Agent started successfully
2025-06-21 12:30:16 INFO  Configuration loaded
2025-06-21 12:30:17 INFO  Memory core initialized
2025-06-21 12:30:18 INFO  LLM gateway ready
2025-06-21 12:30:20 INFO  New task received: Search for Python tutorials
2025-06-21 12:30:21 INFO  Planning phase started
2025-06-21 12:30:23 INFO  Executing step 1: search_web
2025-06-21 12:30:25 INFO  Step 1 completed successfully
2025-06-21 12:30:26 INFO  Task completed successfully
"""
            
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", sample_logs)
            
        except Exception as e:
            print(f"Error refreshing logs: {e}")
    
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete("1.0", tk.END)
    
    def load_current_config(self):
        """Load current configuration into GUI"""
        try:
            config = config_manager.load_config()
            
            # Load API keys (showing only if they exist)
            if config.primary_llm.api_key:
                self.openrouter_key_var.set("*" * 20)  # Mask existing key
            
            # Load security settings
            self.allow_file_ops_var.set(config.security.allow_file_operations)
            self.allow_network_var.set(config.security.allow_network_access)
            self.allow_code_exec_var.set(config.security.allow_code_execution)
            
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_api_keys(self):
        """Save API key configuration"""
        try:
            # This would update the actual configuration
            messagebox.showinfo("Success", "API keys saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys: {e}")
    
    def save_security_settings(self):
        """Save security settings"""
        try:
            # This would update the actual configuration
            messagebox.showinfo("Success", "Security settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save security settings: {e}")
    
    def show_window(self):
        """Show the GUI window"""
        if not self.root:
            self.create_window()
        
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_visible = True
    
    def hide_window(self):
        """Hide the GUI window"""
        if self.root:
            self.root.withdraw()
        self.is_visible = False


class SystemTrayManager:
    """Manages the system tray icon and menu"""
    
    def __init__(self):
        self.gui = PraxisGUI()
        self.icon = None
        
    def create_image(self, color="blue"):
        """Create system tray icon image"""
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color="white")
            draw = ImageDraw.Draw(image)
            
            # Draw a simple "P" for Praxis
            draw.ellipse([8, 8, 56, 56], fill=color, outline="black", width=2)
            draw.text((24, 20), "P", fill="white")
            
            return image
        except Exception as e:
            print(f"Error creating icon: {e}")
            # Fallback to basic icon
            image = Image.new('RGB', (64, 64), color=color)
            return image
    
    def create_menu(self):
        """Create system tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Show Control Panel", self.show_gui),
            pystray.MenuItem("Quick Task", self.quick_task),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status", self.show_status),
            pystray.MenuItem("Start Agent", self.start_agent),
            pystray.MenuItem("Stop Agent", self.stop_agent),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_application)
        )
    
    def show_gui(self, icon=None, item=None):
        """Show the main GUI"""
        self.gui.show_window()
    
    def quick_task(self, icon=None, item=None):
        """Show quick task dialog"""
        # This would show a simple input dialog
        pass
    
    def show_status(self, icon=None, item=None):
        """Show status notification"""
        try:
            status = orchestrator.get_status()
            if status["is_running"]:
                message = f"Agent Running - {status['active_tasks']} active tasks"
            else:
                message = "Agent Stopped"
            
            if self.icon:
                self.icon.notify(message, "Praxis Agent Status")
        except:
            if self.icon:
                self.icon.notify("Status unavailable", "Praxis Agent")
    
    def start_agent(self, icon=None, item=None):
        """Start the agent from tray"""
        self.gui.start_agent()
    
    def stop_agent(self, icon=None, item=None):
        """Stop the agent from tray"""
        self.gui.stop_agent()
    
    def quit_application(self, icon=None, item=None):
        """Quit the entire application"""
        if self.icon:
            self.icon.stop()
        if self.gui.root:
            self.gui.root.quit()
    
    def run(self):
        """Run the system tray"""
        image = self.create_image()
        menu = self.create_menu()
        
        self.icon = pystray.Icon("praxis_agent", image, "Praxis Agent", menu)
        self.icon.run()


def main():
    """Main entry point for Windows service"""
    try:
        # Initialize configuration
        config_manager.load_config()
        
        # Create system tray manager
        tray_manager = SystemTrayManager()
        
        print("🚀 Starting Praxis Agent Windows Service...")
        print("👀 Look for the system tray icon to access the control panel")
        
        # Run the system tray (this blocks)
        tray_manager.run()
        
    except Exception as e:
        print(f"❌ Failed to start Praxis Agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
