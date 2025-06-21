"""
Praxis Agent - Next-Generation AI Assistant
A modular, intelligent agent system for Windows with multi-AI provider support
"""

__version__ = "1.0.0"
__author__ = "MiniMax Agent"
__description__ = "Intelligent AI agent with local and cloud AI capabilities"

from core.orchestrator import orchestrator
from config.settings import config_manager
from gateway.llm_gateway import llm_gateway
from cognitive.memory_core import memory_core
from toolkit.actions import action_toolkit

__all__ = [
    "orchestrator",
    "config_manager", 
    "llm_gateway",
    "memory_core",
    "action_toolkit"
]
