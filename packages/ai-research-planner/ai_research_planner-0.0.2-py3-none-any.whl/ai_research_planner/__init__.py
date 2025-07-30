"""AI Research Planner - AI-powered research planning and execution system."""

__version__ = "1.0.0"
__author__ = "AI Research Team"
__email__ = "team@airesearch.com"
__description__ = "AI-powered research planning and execution system"

from ai_research_planner.main import ResearchPlanner
from ai_research_planner.models import ResearchPlan, ResearchResults
from ai_research_planner.planning.plan_generator import PlanGenerator
from ai_research_planner.execution.plan_executor import PlanExecutor

__all__ = [
    "ResearchPlanner",
    "ResearchPlan", 
    "ResearchResults",
    "PlanGenerator",
    "PlanExecutor",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]

# Package metadata for runtime access
def get_version() -> str:
    """Get package version."""
    return __version__

def get_package_info() -> dict:
    """Get complete package information."""
    return {
        "name": "ai-research-planner",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "description": __description__,
        "python_requires": ">=3.8"
    }
