"""AI configuration manager for multi-model support."""

from typing import Dict, List, Optional
from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class AIConfigManager:
    """Manages AI model configurations and provider switching."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        providers = []
        
        # Check Ollama
        try:
            import ollama
            providers.append('ollama')
        except ImportError:
            pass
        
        # Check OpenAI
        try:
            from openai import OpenAI
            if self.config.get_api_key('openai'):
                providers.append('openai')
        except ImportError:
            pass
        
        # Check Anthropic
        try:
            import anthropic
            if self.config.get_api_key('anthropic'):
                providers.append('anthropic')
        except ImportError:
            pass
        
        return providers
    
    def get_available_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """Get available models for provider(s)."""
        alt_models = self.config.get('ai_model.alternative_models', {})
        
        if provider:
            return {provider: alt_models.get(provider, {}).get('models', [])}
        
        return {p: data.get('models', []) for p, data in alt_models.items()}
    
    def switch_provider(self, provider: str, model_name: Optional[str] = None) -> bool:
        """Switch to different AI provider."""
        available_providers = self.get_available_providers()
        
        if provider not in available_providers:
            logger.error(f"Provider {provider} not available")
            return False
        
        # Set provider
        self.config.set('ai_model.provider', provider)
        
        # Set model if specified
        if model_name:
            available_models = self.get_available_models(provider).get(provider, [])
            if model_name in available_models:
                self.config.set('ai_model.model_name', model_name)
            else:
                logger.warning(f"Model {model_name} not available for {provider}")
                # Use first available model
                if available_models:
                    self.config.set('ai_model.model_name', available_models[0])
        
        # Update base URL
        provider_config = self.config.get(f'ai_model.alternative_models.{provider}', {})
        if 'base_url' in provider_config:
            self.config.set('ai_model.base_url', provider_config['base_url'])
        
        logger.info(f"Switched to provider: {provider}")
        return True
    
    def validate_provider_setup(self, provider: str) -> Dict[str, bool]:
        """Validate provider setup."""
        validation = {
            'provider_available': False,
            'api_key_configured': True,  # Default true for local providers
            'models_available': False
        }
        
        # Check if provider is available
        available_providers = self.get_available_providers()
        validation['provider_available'] = provider in available_providers
        
        # Check API key for external providers
        if provider in ['openai', 'anthropic']:
            api_key = self.config.get_api_key(provider)
            validation['api_key_configured'] = bool(api_key)
        
        # Check models
        models = self.get_available_models(provider).get(provider, [])
        validation['models_available'] = len(models) > 0
        
        return validation
    
    def get_recommended_settings(self, use_case: str) -> Dict[str, any]:
        """Get recommended settings for different use cases."""
        
        recommendations = {
            'research_planning': {
                'temperature': 0.3,
                'max_tokens': 16384,
                'top_p': 0.9
            },
            'data_analysis': {
                'temperature': 0.1,
                'max_tokens': 8192,
                'top_p': 0.8
            },
            'creative_research': {
                'temperature': 0.7,
                'max_tokens': 32768,
                'top_p': 0.95
            },
            'fact_checking': {
                'temperature': 0.0,
                'max_tokens': 4096,
                'top_p': 0.7
            }
        }
        
        return recommendations.get(use_case, recommendations['research_planning'])
