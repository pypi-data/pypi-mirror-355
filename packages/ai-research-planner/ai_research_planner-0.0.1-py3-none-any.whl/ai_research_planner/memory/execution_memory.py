"""Execution memory management for AI Research Planner."""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionMemory:
    """Stores and manages execution state, plans, and results."""
    
    def __init__(self):
        self.plans: List[Any] = []  # Will store ResearchPlan objects
        self.results: List[Any] = []  # Will store ResearchResults objects
        self.execution_logs: List[Dict[str, Any]] = []
        self.session_data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'total_plans': 0,
            'total_results': 0,
            'session_id': self._generate_session_id()
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def store_plan(self, plan: Any) -> None:
        """Store a research plan."""
        self.plans.append(plan)
        self.metadata['total_plans'] = len(self.plans)
        self.metadata['last_updated'] = datetime.now().isoformat()
        
        # Log plan storage
        self.execution_logs.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'plan_stored',
            'plan_id': getattr(plan, 'id', 'unknown'),
            'goal': getattr(plan, 'goal', 'unknown'),
            'complexity': getattr(plan, 'complexity', 'unknown')
        })
        
        logger.debug(f"Stored plan: {getattr(plan, 'goal', 'unknown')}")
    
    def store_results(self, results: Any) -> None:
        """Store research results."""
        self.results.append(results)
        self.metadata['total_results'] = len(self.results)
        self.metadata['last_updated'] = datetime.now().isoformat()
        
        # Log results storage
        self.execution_logs.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'results_stored',
            'result_id': getattr(results, 'id', 'unknown'),
            'plan_id': getattr(results, 'plan_id', 'unknown'),
            'raw_items': len(getattr(results, 'raw_data', [])),
            'cleaned_items': len(getattr(results, 'cleaned_data', []))
        })
        
        logger.debug(f"Stored results for plan: {getattr(results, 'plan_id', 'unknown')}")
    
    def get_all_plans(self) -> List[Any]:
        """Get all stored plans."""
        return self.plans
    
    def get_all_results(self) -> List[Any]:
        """Get all stored results."""
        return self.results
    
    def get_all_scraped_data(self) -> List[Dict[str, Any]]:
        """Get all scraped data from stored results."""
        all_data = []
        for result in self.results:
            if hasattr(result, 'raw_data'):
                all_data.extend(result.raw_data)
        return all_data
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary statistics."""
        total_scraped_items = sum(
            len(getattr(result, 'raw_data', []))
            for result in self.results
        )
        
        total_cleaned_items = sum(
            len(getattr(result, 'cleaned_data', []))
            for result in self.results
        )
        
        # Calculate success rate from execution logs
        plan_actions = [log for log in self.execution_logs if log.get('action') == 'plan_stored']
        result_actions = [log for log in self.execution_logs if log.get('action') == 'results_stored']
        
        success_rate = len(result_actions) / len(plan_actions) if plan_actions else 0
        
        return {
            'session_id': self.metadata['session_id'],
            'total_steps': len(self.execution_logs),
            'successful_steps': len(result_actions),
            'failed_steps': len(plan_actions) - len(result_actions),
            'success_rate': success_rate,
            'total_scraped_items': total_scraped_items,
            'total_cleaned_items': total_cleaned_items,
            'unique_domains': self._count_unique_domains(),
            'total_execution_time': 0,  # Would need timing implementation
            'average_execution_time': 0.0,
            'action_breakdown': self._get_action_breakdown(),
            'session_duration': self._calculate_session_duration(),
            'last_updated': self.metadata['last_updated']
        }
    
    def _count_unique_domains(self) -> int:
        """Count unique domains from scraped data."""
        from urllib.parse import urlparse
        
        domains = set()
        for result in self.results:
            if hasattr(result, 'raw_data'):
                for item in result.raw_data:
                    if hasattr(item, 'url') or (isinstance(item, dict) and 'url' in item):
                        url = item.url if hasattr(item, 'url') else item['url']
                        try:
                            domain = urlparse(url).netloc
                            if domain:
                                domains.add(domain)
                        except:
                            continue
        return len(domains)
    
    def _get_action_breakdown(self) -> Dict[str, int]:
        """Get breakdown of actions performed."""
        breakdown = {}
        for log in self.execution_logs:
            action = log.get('action', 'unknown')
            breakdown[action] = breakdown.get(action, 0) + 1
        return breakdown
    
    def _calculate_session_duration(self) -> float:
        """Calculate session duration in seconds."""
        created_at = datetime.fromisoformat(self.metadata['created_at'])
        last_updated = datetime.fromisoformat(self.metadata['last_updated'])
        return (last_updated - created_at).total_seconds()
    
    def add_execution_result(self, step: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Add execution result for a step."""
        self.execution_logs.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'step_executed',
            'step': step,
            'result': result,
            'status': result.get('status', 'unknown')
        })
        
        self.metadata['last_updated'] = datetime.now().isoformat()
    
    def set_context(self, key: str, value: Any) -> None:
        """Set context data for the session."""
        self.session_data[key] = value
        self.metadata['last_updated'] = datetime.now().isoformat()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context data from the session."""
        return self.session_data.get(key, default)
    
    def export_memory(self, filepath: str) -> None:
        """Export memory to JSON file."""
        # Prepare serializable data
        plans_data = []
        for plan in self.plans:
            if hasattr(plan, 'to_json'):
                plans_data.append(json.loads(plan.to_json()))
            else:
                plans_data.append(str(plan))
        
        results_data = []
        for result in self.results:
            if hasattr(result, 'get_summary'):
                results_data.append(result.get_summary())
            else:
                results_data.append(str(result))
        
        data = {
            'metadata': self.metadata,
            'plans': plans_data,
            'results': results_data,
            'execution_logs': self.execution_logs,
            'session_data': self.session_data,
            'export_timestamp': datetime.now().isoformat()
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Memory exported to {filepath}")
    
    def clear_memory(self) -> None:
        """Clear all stored plans and results."""
        self.plans.clear()
        self.results.clear()
        self.execution_logs.clear()
        self.session_data.clear()
        
        self.metadata.update({
            'total_plans': 0,
            'total_results': 0,
            'last_updated': datetime.now().isoformat(),
            'session_id': self._generate_session_id()
        })
        
        logger.info("Execution memory cleared")
    
    def load_memory(self, filepath: str) -> None:
        """Load memory from JSON file."""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Memory file not found: {filepath}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.metadata = data.get('metadata', self.metadata)
            self.execution_logs = data.get('execution_logs', [])
            self.session_data = data.get('session_data', {})
            
            # Note: Plans and results would need proper deserialization
            # This is a simplified version
            logger.info(f"Memory loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load memory from {filepath}: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of memory state."""
        return {
            **self.metadata,
            'execution_logs_count': len(self.execution_logs),
            'session_data_keys': list(self.session_data.keys())
        }
    
    def find_plan_by_goal(self, goal: str) -> Optional[Any]:
        """Find a plan by its goal."""
        for plan in self.plans:
            if hasattr(plan, 'goal') and plan.goal == goal:
                return plan
        return None
    
    def find_results_by_plan_id(self, plan_id: str) -> Optional[Any]:
        """Find results by plan ID."""
        for result in self.results:
            if hasattr(result, 'plan_id') and result.plan_id == plan_id:
                return result
        return None
    
    def get_latest_plan(self) -> Optional[Any]:
        """Get the most recently stored plan."""
        return self.plans[-1] if self.plans else None
    
    def get_latest_results(self) -> Optional[Any]:
        """Get the most recently stored results."""
        return self.results[-1] if self.results else None
