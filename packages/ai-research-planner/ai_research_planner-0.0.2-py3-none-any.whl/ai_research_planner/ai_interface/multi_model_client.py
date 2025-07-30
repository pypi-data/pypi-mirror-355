"""Multi-model AI client supporting Ollama, OpenAI, and Anthropic."""

import os
import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import different AI clients
import ollama

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class MultiModelClient:
    """Multi-provider AI client with selective initialization."""
    
    def __init__(self, config: Config):
        self.config = config
        self.provider = config.get('ai_model.provider', 'ollama')
        self.model_name = config.get('ai_model.model_name', 'deepseek-r1:latest')
        self.base_url = config.get('ai_model.base_url', 'http://localhost:11434')
        self.temperature = config.get('ai_model.temperature', 0.6)
        self.max_tokens = config.get('ai_model.max_tokens', 32768)
        self.top_p = config.get('ai_model.top_p', 0.95)
        self.hybrid_mode = config.get('ai_model.hybrid_mode', True)
        self.training_data_info = self._get_training_data_info()
        self.connection_verified = False
        
        # Initialize only the configured provider (FIXED)
        self._init_configured_provider()
    
    def _init_configured_provider(self):
        """Initialize only the configured AI provider to avoid warnings."""
        self.clients = {}
        
        logger.info(f"Initializing {self.provider} provider...")
        
        try:
            if self.provider == 'ollama':
                self.clients['ollama'] = self._init_ollama()
                self.connection_verified = True
                logger.info(f"✅ {self.provider} initialized successfully")
            elif self.provider == 'openai':
                self.clients['openai'] = self._init_openai()
                self.connection_verified = True
                logger.info(f"✅ {self.provider} initialized successfully")
            elif self.provider == 'anthropic':
                self.clients['anthropic'] = self._init_anthropic()
                self.connection_verified = True
                logger.info(f"✅ {self.provider} initialized successfully")
            else:
                logger.error(f"Unknown provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider}: {e}")
            self.connection_verified = False
    
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
        
        if self.model_name not in available_models:
            logger.warning(f"Model {self.model_name} not found. Available: {available_models}")
            if available_models:
                self.model_name = available_models[0]
                logger.info(f"Using fallback model: {self.model_name}")
        
        return True
    
    def _init_openai(self):
        """Initialize OpenAI client with config file API key support."""
        if not OpenAI:
            raise ImportError("OpenAI package not installed")
        
        api_key = self.config.get_api_key('openai')
        
        if api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                # Test the connection
                test_response = self.openai_client.models.list()
                logger.info("OpenAI client initialized successfully")
                return True
            except Exception as e:
                logger.error(f"OpenAI client initialization failed: {e}")
                raise
        else:
            raise ValueError("OpenAI API key not found in environment or config file")
    
    def _init_anthropic(self):
        """Initialize Anthropic client with config file API key support."""
        if not anthropic:
            raise ImportError("Anthropic package not installed")
        
        api_key = self.config.get_api_key('anthropic')
        
        if api_key:
            try:
                client = anthropic.Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized successfully")
                return client
            except Exception as e:
                logger.error(f"Anthropic client initialization failed: {e}")
                raise
        else:
            raise ValueError("Anthropic API key not found in environment or config file")
    
    def _get_training_data_info(self) -> Dict[str, str]:
        """Get training data information for different models."""
        training_cutoffs = {
            'deepseek-r1:latest': 'October 2024',
            'llama3.2:latest': 'September 2024',
            'mistral:latest': 'September 2024',
            'gpt-4': 'April 2024',
            'gpt-4o-mini': 'October 2023',
            'gpt-3.5-turbo': 'September 2021',
            'claude-3-opus': 'August 2023',
            'claude-3-sonnet': 'August 2023'
        }
        
        return {
            'model': self.model_name,
            'provider': self.provider,
            'training_cutoff': training_cutoffs.get(self.model_name, 'Unknown'),
        }
    
    def is_connected(self) -> bool:
        """Check if the configured AI provider is connected."""
        return self.connection_verified and self.provider in self.clients
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None,
                              temperature: Optional[float] = None) -> str:
        """Generate response using configured AI provider."""
        if not self.is_connected():
            raise RuntimeError(f"AI provider {self.provider} is not connected")
            
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
        return self.training_data_info
