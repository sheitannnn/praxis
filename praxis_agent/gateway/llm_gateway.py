"""
LLM Gateway - Unified interface for multiple AI providers
Supports OpenRouter, Ollama, OpenAI, and Anthropic
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import LLMConfig, AIProvider, config_manager


@dataclass
class LLMResponse:
    """Standardized response from LLM providers"""
    content: str
    model: str
    provider: str
    tokens_used: int
    cost_usd: Optional[float] = None
    latency_ms: int = 0
    success: bool = True
    error: Optional[str] = None


class LLMGateway:
    """Unified interface for multiple LLM providers"""
    
    def __init__(self):
        self.config = config_manager.load_config()
        self.session = self._create_session()
        self.token_usage = {"total": 0, "session": 0}
        self.cost_tracking = {"total": 0.0, "session": 0.0}
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                      use_fallback: bool = False, **kwargs) -> LLMResponse:
        """Generate response using configured LLM"""
        start_time = time.time()
        
        # Select LLM config
        llm_config = self.config.fallback_llm if use_fallback else self.config.primary_llm
        if not llm_config:
            return LLMResponse("", "", "", 0, error="No LLM configuration available")
        
        try:
            # Route to appropriate provider
            if llm_config.provider == AIProvider.OPENROUTER:
                response = await self._call_openrouter(prompt, system_prompt, llm_config, **kwargs)
            elif llm_config.provider == AIProvider.OLLAMA:
                response = await self._call_ollama(prompt, system_prompt, llm_config, **kwargs)
            elif llm_config.provider == AIProvider.OPENAI:
                response = await self._call_openai(prompt, system_prompt, llm_config, **kwargs)
            elif llm_config.provider == AIProvider.ANTHROPIC:
                response = await self._call_anthropic(prompt, system_prompt, llm_config, **kwargs)
            else:
                return LLMResponse("", "", "", 0, error=f"Unsupported provider: {llm_config.provider}")
            
            # Calculate latency
            response.latency_ms = int((time.time() - start_time) * 1000)
            
            # Update usage tracking
            self.token_usage["total"] += response.tokens_used
            self.token_usage["session"] += response.tokens_used
            if response.cost_usd:
                self.cost_tracking["total"] += response.cost_usd
                self.cost_tracking["session"] += response.cost_usd
            
            return response
            
        except Exception as e:
            return LLMResponse("", "", "", 0, error=str(e), latency_ms=int((time.time() - start_time) * 1000))
    
    async def _call_openrouter(self, prompt: str, system_prompt: Optional[str], 
                              config: LLMConfig, **kwargs) -> LLMResponse:
        """Call OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/praxis-agent",
            "X-Title": "Praxis Agent"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": config.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "stream": False
        }
        
        response = self.session.post(
            f"{config.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", config.model),
            provider="openrouter",
            tokens_used=usage.get("total_tokens", 0),
            cost_usd=self._calculate_openrouter_cost(usage, config.model)
        )
    
    async def _call_ollama(self, prompt: str, system_prompt: Optional[str], 
                          config: LLMConfig, **kwargs) -> LLMResponse:
        """Call Ollama local API"""
        payload = {
            "model": config.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", config.temperature),
                "num_predict": kwargs.get("max_tokens", config.max_tokens)
            }
        }
        
        response = self.session.post(
            f"{config.base_url}/api/generate",
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        
        return LLMResponse(
            content=data.get("response", ""),
            model=config.model,
            provider="ollama",
            tokens_used=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            cost_usd=0.0  # Local models are free
        )
    
    async def _call_openai(self, prompt: str, system_prompt: Optional[str], 
                          config: LLMConfig, **kwargs) -> LLMResponse:
        """Call OpenAI API directly"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": config.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature)
        }
        
        response = self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", config.model),
            provider="openai",
            tokens_used=usage.get("total_tokens", 0),
            cost_usd=self._calculate_openai_cost(usage, config.model)
        )
    
    async def _call_anthropic(self, prompt: str, system_prompt: Optional[str], 
                             config: LLMConfig, **kwargs) -> LLMResponse:
        """Call Anthropic API"""
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": config.model,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature),
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = self.session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        
        return LLMResponse(
            content=data["content"][0]["text"],
            model=config.model,
            provider="anthropic",
            tokens_used=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
            cost_usd=self._calculate_anthropic_cost(data.get("usage", {}), config.model)
        )
    
    def _calculate_openrouter_cost(self, usage: Dict, model: str) -> Optional[float]:
        """Calculate approximate cost for OpenRouter usage"""
        # This would need to be updated with actual OpenRouter pricing
        # For now, return None as costs vary by model
        return None
    
    def _calculate_openai_cost(self, usage: Dict, model: str) -> Optional[float]:
        """Calculate OpenAI API cost based on usage"""
        # Simplified pricing - update with current rates
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
        
        base_model = model.split("-")[0] + "-" + model.split("-")[1] if "-" in model else model
        if base_model in pricing:
            input_cost = (usage.get("prompt_tokens", 0) / 1000) * pricing[base_model]["input"]
            output_cost = (usage.get("completion_tokens", 0) / 1000) * pricing[base_model]["output"]
            return input_cost + output_cost
        
        return None
    
    def _calculate_anthropic_cost(self, usage: Dict, model: str) -> Optional[float]:
        """Calculate Anthropic API cost based on usage"""
        # Simplified pricing - update with current rates
        pricing = {
            "claude-3": {"input": 0.015, "output": 0.075},
            "claude-2": {"input": 0.008, "output": 0.024}
        }
        
        base_model = "claude-3" if "claude-3" in model else "claude-2"
        if base_model in pricing:
            input_cost = (usage.get("input_tokens", 0) / 1000) * pricing[base_model]["input"]
            output_cost = (usage.get("output_tokens", 0) / 1000) * pricing[base_model]["output"]
            return input_cost + output_cost
        
        return None
    
    def get_available_models(self, provider: AIProvider) -> List[str]:
        """Get list of available models for a provider"""
        if provider == AIProvider.OLLAMA:
            try:
                response = self.session.get(f"{self.config.fallback_llm.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
            except:
                pass
            return ["llama2:7b", "llama2:13b", "codellama:7b", "mistral:7b"]
        
        elif provider == AIProvider.OPENROUTER:
            # Return common OpenRouter models
            return [
                "openai/gpt-4-turbo-preview",
                "openai/gpt-3.5-turbo",
                "anthropic/claude-3-opus",
                "anthropic/claude-3-sonnet",
                "mistralai/mistral-7b-instruct",
                "meta-llama/llama-2-70b-chat"
            ]
        
        return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            "tokens": self.token_usage.copy(),
            "costs": self.cost_tracking.copy(),
            "primary_model": self.config.primary_llm.model,
            "fallback_model": self.config.fallback_llm.model if self.config.fallback_llm else None
        }
    
    def reset_session_stats(self) -> None:
        """Reset session statistics"""
        self.token_usage["session"] = 0
        self.cost_tracking["session"] = 0.0


# Global gateway instance
llm_gateway = LLMGateway()
