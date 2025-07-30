"""Multi-model AI client supporting Ollama, OpenAI, and Anthropic."""

import os
import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import AI clients
import ollama

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class MultiModelClient:
    """Multi-provider AI client for research planning."""
    
    def __init__(self, config: Config):
        self.config = config
        self.provider = config.get('ai_model.provider', 'ollama')
        self.model_name = config.get('ai_model.model_name', 'deepseek-r1:latest')
        self.base_url = config.get('ai_model.base_url', 'http://localhost:11434')
        self.temperature = config.get('ai_model.temperature', 0.6)
        self.max_tokens = config.get('ai_model.max_tokens', 32768)
        self.top_p = config.get('ai_model.top_p', 0.95)
        self.connection_verified = False
        
        # Initialize clients
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all available AI providers."""
        self.clients = {}
        
        # Initialize Ollama
        try:
            self.clients['ollama'] = self._init_ollama()
            self.connection_verified = True
        except Exception as e:
            logger.warning(f"Ollama initialization failed: {e}")
        
        # Initialize OpenAI
        try:
            self.clients['openai'] = self._init_openai()
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
        
        # Initialize Anthropic
        try:
            self.clients['anthropic'] = self._init_anthropic()
        except Exception as e:
            logger.warning(f"Anthropic initialization failed: {e}")
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        response = ollama.list()
        models_data = response.get('models', [])
        
        available_models = []
        for model in models_data:
            try:
                if hasattr(model, 'model'):
                    model_name = model.model
                elif hasattr(model, 'name'):
                    model_name = model.name
                elif isinstance(model, dict):
                    model_name = model.get('name') or model.get('model')
                else:
                    continue
                available_models.append(model_name)
            except:
                continue
        
        logger.info(f"Ollama available models: {available_models}")
        
        if self.model_name not in available_models and available_models:
            self.model_name = available_models[0]
            logger.info(f"Using fallback model: {self.model_name}")
        
        return True
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        if not OpenAI:
            return None
        
        api_key = self.config.get_api_key('openai')
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
            return True
        return None
    
    def _init_anthropic(self):
        """Initialize Anthropic client."""
        if not anthropic:
            return None
        
        api_key = self.config.get_api_key('anthropic')
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized")
            return client
        return None
    
    def is_connected(self) -> bool:
        """Check if at least one AI provider is connected."""
        return self.connection_verified or any(self.clients.values())
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None,
                              temperature: Optional[float] = None) -> str:
        """Generate response using configured AI provider."""
        if self.provider == 'ollama':
            return await self._generate_ollama_response(prompt, system_prompt, temperature)
        elif self.provider == 'openai':
            return await self._generate_openai_response(prompt, system_prompt, temperature)
        elif self.provider == 'anthropic':
            return await self._generate_anthropic_response(prompt, system_prompt, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _generate_ollama_response(self, prompt: str, system_prompt: Optional[str] = None,
                                      temperature: Optional[float] = None) -> str:
        """Generate response using Ollama."""
        messages = []
        
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        messages.append({'role': 'user', 'content': prompt})
        
        response = ollama.chat(
            model=self.model_name,
            messages=messages,
            options={
                'temperature': temperature or self.temperature,
                'num_predict': self.max_tokens,
                'top_p': self.top_p,
            }
        )
        
        return response['message']['content']
    
    async def _generate_openai_response(self, prompt: str, system_prompt: Optional[str] = None,
                                      temperature: Optional[float] = None) -> str:
        """Generate response using OpenAI."""
        if not hasattr(self, 'openai_client'):
            raise RuntimeError("OpenAI client not initialized")
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        messages.append({'role': 'user', 'content': prompt})
        
        completion = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens
        )
        
        return completion.choices[0].message.content
    
    async def _generate_anthropic_response(self, prompt: str, system_prompt: Optional[str] = None,
                                         temperature: Optional[float] = None) -> str:
        """Generate response using Anthropic."""
        if 'anthropic' not in self.clients or not self.clients['anthropic']:
            raise RuntimeError("Anthropic client not initialized")
        
        client = self.clients['anthropic']
        
        full_prompt = ""
        if system_prompt:
            full_prompt += f"System: {system_prompt}\n\n"
        full_prompt += f"Human: {prompt}\n\nAssistant:"
        
        response = client.completions.create(
            model=self.model_name,
            prompt=full_prompt,
            max_tokens_to_sample=self.max_tokens,
            temperature=temperature or self.temperature
        )
        
        return response.completion
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about current model."""
        training_cutoffs = {
            'deepseek-r1:latest': 'October 2024',
            'llama3.2:latest': 'September 2024',
            'mistral:latest': 'September 2024',
            'gpt-4': 'April 2024',
            'gpt-3.5-turbo': 'September 2021',
            'claude-3-opus': 'August 2023',
            'claude-3-sonnet': 'August 2023'
        }
        
        return {
            'provider': self.provider,
            'model_name': self.model_name,
            'training_cutoff': training_cutoffs.get(self.model_name, 'Unknown'),
            'base_url': self.base_url
        }
