"""Data models for research plans and results."""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field, MISSING
from pathlib import Path

try:
    from ai_research_planner.utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class ResearchStep:
    """Represents a single step in a research plan."""
    action: str
    tool: str
    parameters: Dict[str, Any]
    description: str
    expected_output: str
    priority: int = 1
    estimated_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchStep':
        """Create from dictionary."""
        return cls(**data)


class DataItem:
    """Represents a single piece of research data - accepts all fields."""
    
    def __init__(self, **kwargs):
        """Accept any keyword arguments to prevent initialization errors."""
        
        # Set default values for required fields
        self.url = kwargs.get('url', '')
        self.title = kwargs.get('title', '')
        self.content = kwargs.get('content', '')
        self.source_type = kwargs.get('source_type', 'web')
        self.timestamp = kwargs.get('timestamp', '')
        self.metadata = kwargs.get('metadata', {})
        self.links = kwargs.get('links', [])
        self.status = kwargs.get('status', 'success')
        self.word_count = kwargs.get('word_count', 0)
        self.error = kwargs.get('error', None)
        self.quality_score = kwargs.get('quality_score', 0.0)
        self.domain = kwargs.get('domain', '')
        
        # Handle any additional unknown fields by storing them in metadata
        known_fields = {
            'url', 'title', 'content', 'source_type', 'timestamp', 
            'metadata', 'links', 'status', 'word_count', 'error', 
            'quality_score', 'domain'
        }
        
        unknown_fields = {k: v for k, v in kwargs.items() if k not in known_fields}
        if unknown_fields:
            if not isinstance(self.metadata, dict):
                self.metadata = {}
            self.metadata.update(unknown_fields)
        
        # Post-initialization setup
        self._post_init()
    
    def _post_init(self):
        """Post initialization setup."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if self.links is None:
            self.links = []
        elif not isinstance(self.links, list):
            self.links = []
        
        if self.word_count == 0 and self.content:
            self.word_count = len(str(self.content).split())
        
        if not self.domain and self.url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                self.domain = parsed.netloc
            except:
                self.domain = ""
        
        # Ensure metadata is a dict
        if not isinstance(self.metadata, dict):
            self.metadata = {}


class ResearchPlan:
    """Represents a complete research plan."""
    
    def __init__(self, goal: str, complexity: str = "standard"):
        self.id = str(uuid.uuid4())
        self.goal = goal
        self.complexity = complexity
        self.steps: List[ResearchStep] = []
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def add_step(self, action: str, tool: str, parameters: Dict[str, Any], 
                 description: str, expected_output: str = "", priority: int = 1) -> None:
        """Add a step to the research plan."""
        step = ResearchStep(
            action=action,
            tool=tool,
            parameters=parameters,
            description=description,
            expected_output=expected_output,
            priority=priority
        )
        self.steps.append(step)
        logger.debug(f"Added step to plan: {description}")
    
    def remove_step(self, index: int) -> None:
        """Remove a step by index."""
        if 0 <= index < len(self.steps):
            removed = self.steps.pop(index)
            logger.debug(f"Removed step: {removed.description}")
    
    def validate(self) -> bool:
        """Validate the research plan."""
        if not self.goal:
            logger.error("Plan validation failed: No goal specified")
            return False
        
        if not self.steps:
            logger.error("Plan validation failed: No steps defined")
            return False
        
        # Check each step has required fields
        for i, step in enumerate(self.steps):
            if not all([step.action, step.tool, step.description]):
                logger.error(f"Plan validation failed: Step {i} missing required fields")
                return False
        
        logger.debug("Plan validation passed")
        return True
    
    def estimate_total_time(self) -> float:
        """Estimate total execution time in minutes."""
        return sum(step.estimated_time for step in self.steps)
    
    def to_json(self) -> str:
        """Convert plan to JSON string."""
        data = {
            'id': self.id,
            'goal': self.goal,
            'complexity': self.complexity,
            'steps': [step.to_dict() for step in self.steps],
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'estimated_time': self.estimate_total_time()
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ResearchPlan':
        """Create plan from JSON string."""
        data = json.loads(json_str)
        
        plan = cls(data['goal'], data.get('complexity', 'standard'))
        plan.id = data.get('id', str(uuid.uuid4()))
        plan.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        plan.metadata = data.get('metadata', {})
        
        # Add steps
        for step_data in data.get('steps', []):
            step = ResearchStep.from_dict(step_data)
            plan.steps.append(step)
        
        return plan
    
    def save(self, filepath: str) -> None:
        """Save plan to file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        logger.info(f"Plan saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'ResearchPlan':
        """Load plan from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            json_str = f.read()
        plan = cls.from_json(json_str)
        logger.info(f"Plan loaded from {filepath}")
        return plan


class ResearchResults:
    """Contains results from executing a research plan."""
    
    def __init__(self, plan_id: str, goal: str):
        self.id = str(uuid.uuid4())
        self.plan_id = plan_id
        self.goal = goal
        self.raw_data: List[DataItem] = []
        self.cleaned_data: List[DataItem] = []
        self.execution_log: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {
            'total_sources': 0,
            'successful_steps': 0,
            'failed_steps': 0,
            'data_retention_rate': 0.0
        }
    
    def add_raw_data(self, data_items: List[DataItem]) -> None:
        """Add raw data items."""
        valid_items = [item for item in data_items if item is not None]
        self.raw_data.extend(valid_items)
        self.metadata['total_sources'] = len(self.raw_data)
        logger.debug(f"Added {len(valid_items)} raw data items")
    
    def set_cleaned_data(self, data_items: List[DataItem]) -> None:
        """Set cleaned data items."""
        valid_items = [item for item in data_items if item is not None]
        self.cleaned_data = valid_items
        if self.raw_data:
            retention_rate = len(self.cleaned_data) / len(self.raw_data)
            self.metadata['data_retention_rate'] = retention_rate
        logger.debug(f"Set {len(valid_items)} cleaned data items")
    
    def add_execution_log(self, step: str, status: str, details: Dict[str, Any]) -> None:
        """Add execution log entry."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.execution_log.append(log_entry)
        
        if status == 'success':
            self.metadata['successful_steps'] += 1
        elif status == 'failed':
            self.metadata['failed_steps'] += 1
    
    def get_raw_data(self) -> List[Dict[str, Any]]:
        """Get raw data as list of dictionaries."""
        result = []
        for item in self.raw_data:
            try:
                if hasattr(item, '__dict__'):
                    result.append(item.__dict__)
                else:
                    result.append({
                        'url': getattr(item, 'url', ''),
                        'title': getattr(item, 'title', ''),
                        'content': getattr(item, 'content', ''),
                        'source_type': getattr(item, 'source_type', 'web'),
                        'timestamp': getattr(item, 'timestamp', ''),
                        'metadata': getattr(item, 'metadata', {}),
                        'links': getattr(item, 'links', []),
                        'status': getattr(item, 'status', 'success'),
                        'word_count': getattr(item, 'word_count', 0),
                        'error': getattr(item, 'error', None),
                        'quality_score': getattr(item, 'quality_score', 0.0),
                        'domain': getattr(item, 'domain', '')
                    })
            except Exception as e:
                logger.warning(f"Error converting DataItem to dict: {e}")
                continue
        return result
    
    def get_cleaned_data(self) -> List[Dict[str, Any]]:
        """Get cleaned data as list of dictionaries."""
        result = []
        for item in self.cleaned_data:
            try:
                if hasattr(item, '__dict__'):
                    result.append(item.__dict__)
                else:
                    result.append({
                        'url': getattr(item, 'url', ''),
                        'title': getattr(item, 'title', ''),
                        'content': getattr(item, 'content', ''),
                        'source_type': getattr(item, 'source_type', 'web'),
                        'timestamp': getattr(item, 'timestamp', ''),
                        'metadata': getattr(item, 'metadata', {}),
                        'links': getattr(item, 'links', []),
                        'status': getattr(item, 'status', 'success'),
                        'word_count': getattr(item, 'word_count', 0),
                        'error': getattr(item, 'error', None),
                        'quality_score': getattr(item, 'quality_score', 0.0),
                        'domain': getattr(item, 'domain', '')
                    })
            except Exception as e:
                logger.warning(f"Error converting DataItem to dict: {e}")
                continue
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of results."""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'goal': self.goal,
            'created_at': self.created_at.isoformat(),
            'total_raw_items': len(self.raw_data),
            'total_cleaned_items': len(self.cleaned_data),
            'execution_steps': len(self.execution_log),
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert results to JSON string for variable storage."""
        return json.dumps({
            'summary': self.get_summary(),
            'raw_data': self.get_raw_data(),
            'cleaned_data': self.get_cleaned_data(),
            'execution_log': self.execution_log
        }, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for variable storage."""
        return {
            'summary': self.get_summary(),
            'raw_data': self.get_raw_data(),
            'cleaned_data': self.get_cleaned_data(),
            'execution_log': self.execution_log
        }
    
    def save(self, output_dir: str) -> None:
        """Save results to directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save raw data
        with open(output_path / "raw_data.json", 'w', encoding='utf-8') as f:
            json.dump(self.get_raw_data(), f, indent=2, ensure_ascii=False)
        
        # Save cleaned data
        with open(output_path / "cleaned_data.json", 'w', encoding='utf-8') as f:
            json.dump(self.get_cleaned_data(), f, indent=2, ensure_ascii=False)
        
        # Save summary and execution log
        with open(output_path / "summary.json", 'w', encoding='utf-8') as f:
            summary_data = self.get_summary()
            summary_data['execution_log'] = self.execution_log
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_dir}")
    
    @classmethod
    def load(cls, output_dir: str) -> 'ResearchResults':
        """Load results from directory."""
        output_path = Path(output_dir)
        
        # Load summary
        with open(output_path / "summary.json", 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Create results object
        results = cls(summary_data['plan_id'], summary_data['goal'])
        results.id = summary_data['id']
        results.created_at = datetime.fromisoformat(summary_data['created_at'])
        results.metadata = summary_data.get('metadata', {})
        results.execution_log = summary_data.get('execution_log', [])
        
        # Load raw data
        try:
            with open(output_path / "raw_data.json", 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            results.raw_data = [DataItem(**item) for item in raw_data]
        except FileNotFoundError:
            logger.warning("Raw data file not found")
        
        # Load cleaned data
        try:
            with open(output_path / "cleaned_data.json", 'r', encoding='utf-8') as f:
                cleaned_data = json.load(f)
            results.cleaned_data = [DataItem(**item) for item in cleaned_data]
        except FileNotFoundError:
            logger.warning("Cleaned data file not found")
        
        logger.info(f"Results loaded from {output_dir}")
        return results
