"""
Configuration management for Praxis Agent
Handles settings for AI providers, system configuration, and user preferences
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum

class AIProvider(str, Enum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class LLMConfig(BaseModel):
    provider: AIProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60

class SystemConfig(BaseModel):
    log_level: LogLevel = LogLevel.INFO
    max_log_files: int = 10
    log_rotation_mb: int = 10
    enable_system_tray: bool = True
    auto_start: bool = True
    max_concurrent_tasks: int = 3
    sandbox_enabled: bool = True

class SecurityConfig(BaseModel):
    allow_file_operations: bool = True
    allow_network_access: bool = True
    allow_code_execution: bool = True
    restricted_paths: List[str] = Field(default_factory=lambda: [
        "C:\\Windows\\System32",
        "C:\\Program Files",
        "C:\\Users\\*\\AppData\\Roaming\\Microsoft"
    ])
    max_file_size_mb: int = 100

class PraxisConfig(BaseModel):
    # AI Configuration
    primary_llm: LLMConfig
    fallback_llm: Optional[LLMConfig] = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # System Configuration
    system: SystemConfig = Field(default_factory=SystemConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Paths
    data_dir: str = "./data"
    logs_dir: str = "./logs" 
    memory_db_path: str = "./data/memory.db"
    vector_db_path: str = "./data/vector_store"
    
    # Memory Configuration
    max_short_term_memories: int = 100
    max_long_term_memories: int = 10000
    memory_retention_days: int = 30

class ConfigManager:
    """Manages configuration loading, saving, and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "config/praxis_config.yaml")
        self.config: Optional[PraxisConfig] = None
        
    def load_config(self) -> PraxisConfig:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f)
                self.config = PraxisConfig(**data)
                return self.config
            except Exception as e:
                print(f"Error loading config: {e}")
                print("Creating default configuration...")
        
        # Create default configuration
        self.config = self._create_default_config()
        self.save_config()
        return self.config
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        if not self.config:
            return
            
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict with proper enum handling
        config_dict = self.config.model_dump(mode='json')
        
        # Convert enum values to strings manually
        if 'primary_llm' in config_dict and 'provider' in config_dict['primary_llm']:
            config_dict['primary_llm']['provider'] = str(config_dict['primary_llm']['provider'])
        if 'fallback_llm' in config_dict and config_dict['fallback_llm'] and 'provider' in config_dict['fallback_llm']:
            config_dict['fallback_llm']['provider'] = str(config_dict['fallback_llm']['provider'])
        if 'system' in config_dict and 'log_level' in config_dict['system']:
            config_dict['system']['log_level'] = str(config_dict['system']['log_level'])
            
        with open(self.config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def _create_default_config(self) -> PraxisConfig:
        """Create default configuration"""
        return PraxisConfig(
            primary_llm=LLMConfig(
                provider=AIProvider.OPENROUTER,
                model="openai/gpt-4-turbo-preview",
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
                base_url="https://openrouter.ai/api/v1"
            ),
            fallback_llm=LLMConfig(
                provider=AIProvider.OLLAMA,
                model="llama2:7b",
                base_url="http://localhost:11434"
            )
        )
    
    def update_api_key(self, provider: AIProvider, api_key: str) -> None:
        """Update API key for a provider"""
        if not self.config:
            self.load_config()
            
        if self.config.primary_llm.provider == provider:
            self.config.primary_llm.api_key = api_key
        elif self.config.fallback_llm and self.config.fallback_llm.provider == provider:
            self.config.fallback_llm.api_key = api_key
            
        self.save_config()
    
    def get_llm_config(self, primary: bool = True) -> Optional[LLMConfig]:
        """Get LLM configuration"""
        if not self.config:
            self.load_config()
            
        return self.config.primary_llm if primary else self.config.fallback_llm
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        if not self.config:
            issues.append("No configuration loaded")
            return issues
        
        # Check primary LLM
        if not self.config.primary_llm.api_key and self.config.primary_llm.provider != AIProvider.OLLAMA:
            issues.append(f"Missing API key for primary LLM ({self.config.primary_llm.provider})")
        
        # Check directories
        for dir_path in [self.config.data_dir, self.config.logs_dir]:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create directory {dir_path}: {e}")
        
        return issues

# Global config manager instance
config_manager = ConfigManager()
