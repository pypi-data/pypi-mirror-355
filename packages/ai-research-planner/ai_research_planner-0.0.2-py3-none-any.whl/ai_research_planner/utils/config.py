"""Configuration management for AI Research Planner."""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path

from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """Configuration manager with intelligent path resolution and API key support."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = self._find_config_path(config_path)
        self._config = self._load_config_with_fallback()
    
    def _find_config_path(self, user_path: Optional[str] = None) -> str:
        """Find config file with priority-based search."""
        
        # Priority 1: User provided path
        if user_path and Path(user_path).exists():
            return str(Path(user_path).resolve())
        
        # Priority 2: Environment variable
        env_config = os.getenv('RESEARCH_PLANNER_CONFIG')
        if env_config and Path(env_config).exists():
            return str(Path(env_config).resolve())
        
        # Priority 3: Default locations
        possible_paths = [
            Path("config/config.yaml"),
            Path("research_planner_config.yaml"),
            Path.home() / ".research-planner" / "config.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.resolve())
        
        # Priority 4: Create default config
        default_path = Path("config/config.yaml")
        default_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_default_config(default_path)
        return str(default_path.resolve())
    
    def _create_default_config(self, config_path: Path) -> None:
        """Create default configuration file."""
        default_config = self._get_default_config()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created default config at {config_path}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'ai_model': {
                'provider': 'ollama',
                'model_name': 'deepseek-r1:latest',
                'base_url': 'http://localhost:11434',
                'temperature': 0.6,
                'max_tokens': 32768,
                'top_p': 0.95,
                'api_keys': {
                    'openai_api_key': '',
                    'anthropic_api_key': '',
                    'gemini_api_key': ''
                },
                'alternative_models': {
                    'ollama': {
                        'models': ['deepseek-r1:latest', 'llama3.2:latest', 'mistral:latest'],
                        'base_url': 'http://localhost:11434'
                    },
                    'openai': {
                        'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
                        'base_url': 'https://api.openai.com/v1',
                        'api_key': ''
                    },
                    'anthropic': {
                        'models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
                        'base_url': 'https://api.anthropic.com',
                        'api_key': ''
                    }
                }
            },
            'research': {
                'max_sources': 15,
                'default_complexity': 'standard',
                'data_cleaning': {
                    'enabled': True,
                    'min_data_retention': 0.7,
                    'strictness': 'medium'
                },
                'plan_generation': {
                    'max_steps': 10,
                    'include_validation': True,
                    'auto_optimize': True
                }
            },
            'scraping': {
                'timeout': 30,
                'max_retries': 3,
                'concurrent_requests': 10,
                'request_delay': 1.0,
                'user_agents': [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ]
            },
            'storage': {
                'cache_enabled': True,
                'cache_ttl': 3600,
                'data_dir': 'research_data',
                'save_intermediate_results': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/research_planner.log'
            }
        }
    
    def _load_config_with_fallback(self) -> Dict[str, Any]:
        """Load configuration with fallback to defaults."""
        default_config = self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
            
            # Deep merge with defaults
            merged_config = self._deep_merge(default_config, file_config)
            logger.info(f"Configuration loaded from {self.config_path}")
            return merged_config
            
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Using default configuration")
            return default_config
    
    def _deep_merge(self, default: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key with priority: Environment Variable > Config File."""
        
        # Environment variables (highest priority)
        env_vars = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'gemini': 'GEMINI_API_KEY'
        }
        
        env_var = env_vars.get(provider.lower())
        if env_var:
            env_value = os.getenv(env_var)
            if env_value:
                return env_value
        
        # Config file
        config_key = f'ai_model.api_keys.{provider.lower()}_api_key'
        config_value = self.get(config_key)
        if config_value and config_value.strip():
            return config_value.strip()
        
        # Provider-specific config
        provider_key = f'ai_model.alternative_models.{provider.lower()}.api_key'
        provider_value = self.get(provider_key)
        if provider_value and provider_value.strip():
            return provider_value.strip()
        
        return None
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration."""
        validation = {
            'config_file_exists': Path(self.config_path).exists(),
            'config_file_readable': True,
            'ai_model_configured': bool(self.get('ai_model.provider')),
            'research_configured': bool(self.get('research.max_sources')),
            'scraping_configured': bool(self.get('scraping.timeout'))
        }
        
        try:
            with open(self.config_path, 'r') as f:
                yaml.safe_load(f)
        except Exception:
            validation['config_file_readable'] = False
        
        return validation
