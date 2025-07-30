"""Enhanced ResearchPlanner with smart cleaning and variable storage."""

import asyncio
import json
from typing import Optional, Dict, Any

from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger
from ai_research_planner.ai_interface.multi_model_client import MultiModelClient
from ai_research_planner.planning.plan_generator import PlanGenerator
from ai_research_planner.execution.plan_executor import PlanExecutor
from ai_research_planner.models import ResearchPlan, ResearchResults
from ai_research_planner.memory.execution_memory import ExecutionMemory

logger = get_logger(__name__)


class ResearchPlanner:
    """Enhanced AI Research Planner with smart cleaning and variable storage."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Research Planner."""
        self.config = Config(config_path)
        self.ai_client = MultiModelClient(self.config)
        self.plan_generator = PlanGenerator(self.ai_client, self.config)
        self.plan_executor = PlanExecutor(self.ai_client, self.config)
        self.memory = ExecutionMemory()
        
        logger.info("ResearchPlanner initialized successfully")
    
    def should_skip_cleaning_based_on_prompt(self, goal: str) -> bool:
        """Determine if cleaning should be skipped based on user prompt importance."""
        goal_lower = goal.lower()
        
        # High-importance keywords that suggest user wants comprehensive data
        comprehensive_keywords = [
            "comprehensive", "complete", "all", "everything", "detailed",
            "thorough", "extensive", "full", "maximum", "entire", "exhaustive",
            "in-depth", "broad", "wide", "total", "absolute", "every"
        ]
        
        # Quality keywords where cleaning is beneficial
        quality_keywords = [
            "summary", "key points", "main", "important", "highlights",
            "brief", "concise", "filtered", "quality", "best", "top",
            "essential", "critical", "significant", "major"
        ]
        
        # Check for comprehensive keywords (skip cleaning)
        if any(keyword in goal_lower for keyword in comprehensive_keywords):
            logger.info("Detected comprehensive research request - skipping data cleaning")
            return True
        
        # Check for quality keywords (keep cleaning)
        if any(keyword in goal_lower for keyword in quality_keywords):
            logger.info("Detected quality-focused request - enabling data cleaning")
            return False
        
        # Default behavior
        return False
    
    async def create_plan(self, research_goal: str, complexity: str = "standard") -> ResearchPlan:
        """Create a research plan for the given goal."""
        logger.info(f"Creating research plan for: {research_goal}")
        logger.info(f"Complexity level: {complexity}")
        
        try:
            plan = await self.plan_generator.generate_plan(research_goal, complexity)
            
            # Store plan in memory
            self.memory.store_plan(plan)
            
            logger.info(f"Research plan created with {len(plan.steps)} steps")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create research plan: {e}")
            raise
    
    async def execute_plan(self, plan: ResearchPlan, skip_cleaning: Optional[bool] = None) -> ResearchResults:
        """Execute a research plan with smart cleaning control."""
        logger.info(f"Executing research plan: {plan.goal}")
        
        # Smart cleaning decision
        if skip_cleaning is None:
            skip_cleaning = self.should_skip_cleaning_based_on_prompt(plan.goal)
        
        if skip_cleaning:
            # Temporarily disable cleaning
            original_cleaning_enabled = self.config.get('research.data_cleaning.enabled', True)
            self.config.set('research.data_cleaning.enabled', False)
            logger.info("🚫 Data cleaning disabled based on prompt analysis")
        
        try:
            # Execute the plan
            results = await self.plan_executor.execute(plan)
            
            # Store results in memory
            self.memory.store_results(results)
            
            logger.info(f"Plan execution completed. Gathered {len(results.raw_data)} data items")
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute research plan: {e}")
            raise
        finally:
            # Restore original cleaning setting
            if skip_cleaning:
                self.config.set('research.data_cleaning.enabled', original_cleaning_enabled)
    
    async def research(self, goal: str, complexity: str = "standard", 
                      skip_cleaning: Optional[bool] = None) -> ResearchResults:
        """One-shot research with smart cleaning control."""
        logger.info(f"Starting one-shot research: {goal}")
        
        # Create plan
        plan = await self.create_plan(goal, complexity)
        
        # Execute plan with smart cleaning
        results = await self.execute_plan(plan, skip_cleaning)
        
        logger.info("One-shot research completed successfully")
        return results
    
    async def research_to_variable(self, goal: str, complexity: str = "standard",
                                  skip_cleaning: Optional[bool] = None) -> Dict[str, Any]:
        """Research and return results as JSON-serializable dictionary."""
        logger.info(f"Research to variable: {goal}")
        
        results = await self.research(goal, complexity, skip_cleaning)
        
        # Return as dictionary for variable storage
        return results.to_dict()
    
    async def research_to_json(self, goal: str, complexity: str = "standard",
                              skip_cleaning: Optional[bool] = None) -> str:
        """Research and return results as JSON string."""
        logger.info(f"Research to JSON: {goal}")
        
        results = await self.research(goal, complexity, skip_cleaning)
        
        # Return as JSON string
        return results.to_json()
    
    def get_memory(self) -> ExecutionMemory:
        """Get execution memory for accessing stored plans and results."""
        return self.memory
    
    def get_config(self) -> Config:
        """Get configuration object."""
        return self.config
    
    async def validate_setup(self) -> Dict[str, bool]:
        """Validate that the research planner is properly configured."""
        validation = {
            'config_loaded': False,
            'ai_client_connected': False,
            'plan_generator_ready': False,
            'plan_executor_ready': False
        }
        
        try:
            # Check config
            validation['config_loaded'] = self.config.validate_config()['config_file_readable']
            
            # Check AI client
            validation['ai_client_connected'] = self.ai_client.is_connected()
            
            # Check plan generator
            validation['plan_generator_ready'] = await self.plan_generator.validate()
            
            # Check plan executor  
            validation['plan_executor_ready'] = self.plan_executor.validate()
            
            logger.info(f"Setup validation: {validation}")
            return validation
            
        except Exception as e:
            logger.error(f"Setup validation failed: {e}")
            return validation
