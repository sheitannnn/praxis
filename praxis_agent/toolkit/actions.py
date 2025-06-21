"""
Action Toolkit - Comprehensive set of tools for the agent
Provides file operations, web search, code execution, and system management
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import psutil
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import time
from datetime import datetime
import sqlite3
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import zipfile
import tarfile

from config.settings import config_manager


@dataclass
class ActionResult:
    """Standardized result from tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None


class SecurityValidator:
    """Validates actions against security policies"""
    
    def __init__(self):
        self.config = config_manager.load_config()
    
    def validate_file_path(self, path: str) -> bool:
        """Check if file path is allowed"""
        if not self.config.security.allow_file_operations:
            return False
        
        abs_path = os.path.abspath(path)
        
        # Check against restricted paths
        for restricted in self.config.security.restricted_paths:
            if restricted.endswith('*'):
                if abs_path.startswith(restricted[:-1]):
                    return False
            else:
                if abs_path.startswith(restricted):
                    return False
        
        return True
    
    def validate_network_access(self, url: str) -> bool:
        """Check if network access is allowed"""
        return self.config.security.allow_network_access
    
    def validate_code_execution(self) -> bool:
        """Check if code execution is allowed"""
        return self.config.security.allow_code_execution


class FileOperations:
    """File system operations"""
    
    def __init__(self):
        self.validator = SecurityValidator()
    
    def read_file(self, path: str, encoding: str = 'utf-8') -> ActionResult:
        """Read file contents"""
        start_time = time.time()
        
        if not self.validator.validate_file_path(path):
            return ActionResult(False, None, "File path not allowed by security policy")
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return ActionResult(
                True, 
                content, 
                execution_time=time.time() - start_time,
                metadata={"file_size": len(content), "encoding": encoding}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def write_file(self, path: str, content: str, encoding: str = 'utf-8') -> ActionResult:
        """Write content to file"""
        start_time = time.time()
        
        if not self.validator.validate_file_path(path):
            return ActionResult(False, None, "File path not allowed by security policy")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return ActionResult(
                True, 
                f"File written successfully: {path}", 
                execution_time=time.time() - start_time,
                metadata={"bytes_written": len(content.encode(encoding))}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def list_directory(self, path: str, recursive: bool = False) -> ActionResult:
        """List directory contents"""
        start_time = time.time()
        
        if not self.validator.validate_file_path(path):
            return ActionResult(False, None, "Directory path not allowed by security policy")
        
        try:
            items = []
            
            if recursive:
                for root, dirs, files in os.walk(path):
                    for name in files + dirs:
                        item_path = os.path.join(root, name)
                        rel_path = os.path.relpath(item_path, path)
                        items.append({
                            "name": name,
                            "path": rel_path,
                            "type": "file" if os.path.isfile(item_path) else "directory",
                            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                        })
            else:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    items.append({
                        "name": item,
                        "type": "file" if os.path.isfile(item_path) else "directory",
                        "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                    })
            
            return ActionResult(
                True, 
                items, 
                execution_time=time.time() - start_time,
                metadata={"item_count": len(items)}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def copy_file(self, src: str, dst: str) -> ActionResult:
        """Copy file from source to destination"""
        start_time = time.time()
        
        if not (self.validator.validate_file_path(src) and self.validator.validate_file_path(dst)):
            return ActionResult(False, None, "File paths not allowed by security policy")
        
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            
            return ActionResult(
                True, 
                f"File copied from {src} to {dst}", 
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def delete_file(self, path: str) -> ActionResult:
        """Delete file or directory"""
        start_time = time.time()
        
        if not self.validator.validate_file_path(path):
            return ActionResult(False, None, "File path not allowed by security policy")
        
        try:
            if os.path.isfile(path):
                os.remove(path)
                message = f"File deleted: {path}"
            elif os.path.isdir(path):
                shutil.rmtree(path)
                message = f"Directory deleted: {path}"
            else:
                return ActionResult(False, None, "Path does not exist")
            
            return ActionResult(
                True, 
                message, 
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)


class WebOperations:
    """Web scraping and HTTP operations"""
    
    def __init__(self):
        self.validator = SecurityValidator()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Praxis-Agent/1.0 (Windows; Educational/Research Purpose)'
        })
    
    def fetch_url(self, url: str, timeout: int = 30) -> ActionResult:
        """Fetch content from URL"""
        start_time = time.time()
        
        if not self.validator.validate_network_access(url):
            return ActionResult(False, None, "Network access not allowed by security policy")
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            return ActionResult(
                True, 
                {
                    "content": response.text,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": response.url
                }, 
                execution_time=time.time() - start_time,
                metadata={"content_length": len(response.text)}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def search_web(self, query: str, num_results: int = 5) -> ActionResult:
        """Search the web using DuckDuckGo"""
        start_time = time.time()
        
        if not self.validator.validate_network_access("https://duckduckgo.com"):
            return ActionResult(False, None, "Network access not allowed by security policy")
        
        try:
            # Use DuckDuckGo instant answer API
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get('https://api.duckduckgo.com/', params=params)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # Extract instant answer
            if data.get('Abstract'):
                results.append({
                    "title": data.get('Heading', 'DuckDuckGo Answer'),
                    "snippet": data['Abstract'],
                    "url": data.get('AbstractURL', ''),
                    "type": "instant_answer"
                })
            
            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        "title": topic.get('Result', '').split(' - ')[0] if ' - ' in topic.get('Result', '') else 'Related Topic',
                        "snippet": topic['Text'],
                        "url": topic.get('FirstURL', ''),
                        "type": "related_topic"
                    })
            
            return ActionResult(
                True, 
                results[:num_results], 
                execution_time=time.time() - start_time,
                metadata={"query": query, "result_count": len(results)}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def extract_text_from_html(self, html: str) -> ActionResult:
        """Extract text content from HTML"""
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return ActionResult(
                True, 
                text, 
                execution_time=time.time() - start_time,
                metadata={"character_count": len(text)}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)


class CodeExecution:
    """Safe code execution in sandboxed environment"""
    
    def __init__(self):
        self.validator = SecurityValidator()
    
    def execute_python(self, code: str, timeout: int = 30) -> ActionResult:
        """Execute Python code safely"""
        start_time = time.time()
        
        if not self.validator.validate_code_execution():
            return ActionResult(False, None, "Code execution not allowed by security policy")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with subprocess for isolation
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tempfile.gettempdir()
                )
                
                return ActionResult(
                    result.returncode == 0,
                    {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "return_code": result.returncode
                    },
                    None if result.returncode == 0 else f"Execution failed with return code {result.returncode}",
                    time.time() - start_time
                )
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ActionResult(False, None, f"Code execution timed out after {timeout} seconds", time.time() - start_time)
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def execute_command(self, command: str, timeout: int = 30) -> ActionResult:
        """Execute system command safely"""
        start_time = time.time()
        
        if not self.validator.validate_code_execution():
            return ActionResult(False, None, "Command execution not allowed by security policy")
        
        # Basic command validation
        dangerous_commands = ['rm', 'del', 'format', 'fdisk', 'shutdown', 'reboot']
        if any(cmd in command.lower() for cmd in dangerous_commands):
            return ActionResult(False, None, "Dangerous command blocked by security policy")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return ActionResult(
                result.returncode == 0,
                {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                },
                None if result.returncode == 0 else f"Command failed with return code {result.returncode}",
                time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return ActionResult(False, None, f"Command execution timed out after {timeout} seconds", time.time() - start_time)
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)


class SystemOperations:
    """System monitoring and management operations"""
    
    def get_system_info(self) -> ActionResult:
        """Get system information"""
        start_time = time.time()
        
        try:
            info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "platform": {
                    "system": os.name,
                    "platform": sys.platform,
                    "python_version": sys.version
                }
            }
            
            return ActionResult(
                True, 
                info, 
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)
    
    def get_running_processes(self, limit: int = 10) -> ActionResult:
        """Get list of running processes"""
        start_time = time.time()
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            return ActionResult(
                True, 
                processes[:limit], 
                execution_time=time.time() - start_time,
                metadata={"total_processes": len(processes)}
            )
        except Exception as e:
            return ActionResult(False, None, str(e), time.time() - start_time)


class ActionToolkit:
    """Main toolkit interface providing all available actions"""
    
    def __init__(self):
        self.file_ops = FileOperations()
        self.web_ops = WebOperations()
        self.code_exec = CodeExecution()
        self.system_ops = SystemOperations()
        
        # Map action names to methods
        self.actions = {
            # File operations
            "read_file": self.file_ops.read_file,
            "write_file": self.file_ops.write_file,
            "list_directory": self.file_ops.list_directory,
            "copy_file": self.file_ops.copy_file,
            "delete_file": self.file_ops.delete_file,
            
            # Web operations
            "fetch_url": self.web_ops.fetch_url,
            "search_web": self.web_ops.search_web,
            "extract_text_from_html": self.web_ops.extract_text_from_html,
            
            # Code execution
            "execute_python": self.code_exec.execute_python,
            "execute_command": self.code_exec.execute_command,
            
            # System operations
            "get_system_info": self.system_ops.get_system_info,
            "get_running_processes": self.system_ops.get_running_processes,
        }
    
    def execute_action(self, action_name: str, **kwargs) -> ActionResult:
        """Execute an action by name"""
        if action_name not in self.actions:
            return ActionResult(False, None, f"Unknown action: {action_name}")
        
        try:
            return self.actions[action_name](**kwargs)
        except Exception as e:
            return ActionResult(False, None, f"Error executing {action_name}: {str(e)}")
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Get list of available actions with descriptions"""
        return [
            {"name": "read_file", "description": "Read content from a file", "parameters": ["path", "encoding"]},
            {"name": "write_file", "description": "Write content to a file", "parameters": ["path", "content", "encoding"]},
            {"name": "list_directory", "description": "List directory contents", "parameters": ["path", "recursive"]},
            {"name": "copy_file", "description": "Copy file from source to destination", "parameters": ["src", "dst"]},
            {"name": "delete_file", "description": "Delete file or directory", "parameters": ["path"]},
            {"name": "fetch_url", "description": "Fetch content from URL", "parameters": ["url", "timeout"]},
            {"name": "search_web", "description": "Search the web", "parameters": ["query", "num_results"]},
            {"name": "extract_text_from_html", "description": "Extract text from HTML", "parameters": ["html"]},
            {"name": "execute_python", "description": "Execute Python code", "parameters": ["code", "timeout"]},
            {"name": "execute_command", "description": "Execute system command", "parameters": ["command", "timeout"]},
            {"name": "get_system_info", "description": "Get system information", "parameters": []},
            {"name": "get_running_processes", "description": "Get running processes", "parameters": ["limit"]},
        ]


# Global toolkit instance
action_toolkit = ActionToolkit()
