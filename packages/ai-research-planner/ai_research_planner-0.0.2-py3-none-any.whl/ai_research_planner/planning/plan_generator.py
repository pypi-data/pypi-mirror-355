"""AI-powered research plan generator."""

import json
import asyncio
from typing import Dict, Any, List, Optional

from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger
from ai_research_planner.ai_interface.multi_model_client import MultiModelClient
from ai_research_planner.models import ResearchPlan, ResearchStep
from ai_research_planner.planning.plan_templates import PlanTemplates

logger = get_logger(__name__)


class PlanGenerator:
    """Generates research plans using AI models."""
    
    def __init__(self, ai_client: MultiModelClient, config: Config):
        self.ai_client = ai_client
        self.config = config
        self.templates = PlanTemplates()
        
        # Planning parameters
        self.max_steps = config.get('research.plan_generation.max_steps', 10)
        self.include_validation = config.get('research.plan_generation.include_validation', True)
        self.auto_optimize = config.get('research.plan_generation.auto_optimize', True)
    
    async def generate_plan(self, goal: str, complexity: str = "standard") -> ResearchPlan:
        """Generate a research plan for the given goal.
        
        Args:
            goal: Research objective or question
            complexity: Plan complexity ('simple', 'standard', 'deep', 'comprehensive')
            
        Returns:
            ResearchPlan: Generated plan
        """
        logger.info(f"Generating {complexity} research plan for: {goal}")
        
        try:
            # Check if we have a template for this type of research
            template_plan = self.templates.get_template_for_goal(goal)
            
            if template_plan and complexity == "simple":
                # Use template for simple requests
                plan = self._customize_template(template_plan, goal)
            else:
                # Generate custom plan using AI
                plan = await self._generate_ai_plan(goal, complexity)
            
            # Validate plan
            if self.include_validation and not plan.validate():
                logger.warning("Generated plan failed validation, creating fallback")
                plan = self._create_fallback_plan(goal, complexity)
            
            # Optimize plan if enabled
            if self.auto_optimize:
                plan = self._optimize_plan(plan)
            
            logger.info(f"Successfully generated plan with {len(plan.steps)} steps")
            return plan
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            # Return fallback plan
            return self._create_fallback_plan(goal, complexity)
    
    async def _generate_ai_plan(self, goal: str, complexity: str) -> ResearchPlan:
        """Generate plan using AI model."""
        
        complexity_params = self._get_complexity_parameters(complexity)
        
        system_prompt = f"""You are an expert research planning assistant. Create a detailed, step-by-step research plan.

COMPLEXITY LEVEL: {complexity}
- Max steps: {complexity_params['max_steps']}
- Depth: {complexity_params['depth']}
- Sources per topic: {complexity_params['sources_per_topic']}

Available tools and actions:
- web_searcher: search_web, search_academic, search_news
- web_scraper: scrape_url, scrape_multiple_urls
- data_processor: clean_data, extract_keywords, summarize_content
- data_analyzer: analyze_trends, compare_sources, validate_facts

Return ONLY a valid JSON array with this exact format:
[
    {{
        "action": "search_web",
        "tool": "web_searcher", 
        "parameters": {{"query": "specific search terms", "max_results": {complexity_params['sources_per_topic']}}},
        "description": "Brief description of this step",
        "expected_output": "What this step should produce"
    }}
]

IMPORTANT:
1. Each step must have: action, tool, parameters, description, expected_output
2. Use specific, targeted search queries
3. Include data validation and cleaning steps
4. Plan should be logical and comprehensive
5. Limit to {complexity_params['max_steps']} steps maximum"""
        
        prompt = f"""Research Goal: {goal}

Create a comprehensive {complexity} research plan to investigate this topic thoroughly.

Focus on:
1. Finding authoritative and current sources
2. Gathering diverse perspectives 
3. Validating information quality
4. Organizing data systematically

Return only the JSON array of research steps."""
        
        response = await self.ai_client.generate_response(prompt, system_prompt, temperature=0.3)
        
        # Parse response and create plan
        plan_data = self._extract_plan_from_response(response)
        plan = self._create_plan_from_data(goal, complexity, plan_data)
        
        return plan
    
    def _get_complexity_parameters(self, complexity: str) -> Dict[str, Any]:
        """Get parameters for different complexity levels."""
        complexity_map = {
            'simple': {
                'max_steps': 3,
                'depth': 'basic',
                'sources_per_topic': 5,
                'include_validation': False
            },
            'standard': {
                'max_steps': 6,
                'depth': 'moderate',
                'sources_per_topic': 10,
                'include_validation': True
            },
            'deep': {
                'max_steps': 8,
                'depth': 'thorough',
                'sources_per_topic': 15,
                'include_validation': True
            },
            'comprehensive': {
                'max_steps': 10,
                'depth': 'exhaustive',
                'sources_per_topic': 20,
                'include_validation': True
            }
        }
        
        return complexity_map.get(complexity, complexity_map['standard'])
    
    def _extract_plan_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Extract plan data from AI response."""
        try:
            # Try to find JSON in response
            if '```' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                if json_end != -1:
                    json_str = response[json_start:json_end].strip()
                else:
                    json_str = response[json_start:].strip()
            elif '[' in response and ']' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                json_str = response[start:end]
            else:
                json_str = response.strip()
            
            plan_data = json.loads(json_str)
            
            if not isinstance(plan_data, list):
                raise ValueError("Plan data must be a list")
            
            return plan_data
            
        except Exception as e:
            logger.error(f"Failed to extract plan from response: {e}")
            raise
    
    def _create_plan_from_data(self, goal: str, complexity: str, plan_data: List[Dict[str, Any]]) -> ResearchPlan:
        """Create ResearchPlan from extracted data."""
        plan = ResearchPlan(goal, complexity)
        
        for i, step_data in enumerate(plan_data):
            try:
                # Validate required fields
                required_fields = ['action', 'tool', 'parameters', 'description']
                if not all(field in step_data for field in required_fields):
                    logger.warning(f"Step {i} missing required fields, skipping")
                    continue
                
                # Create step
                step = ResearchStep(
                    action=step_data['action'],
                    tool=step_data['tool'],
                    parameters=step_data['parameters'],
                    description=step_data['description'],
                    expected_output=step_data.get('expected_output', ''),
                    priority=i + 1,
                    estimated_time=step_data.get('estimated_time', 5.0)
                )
                
                plan.steps.append(step)
                
            except Exception as e:
                logger.warning(f"Failed to create step {i}: {e}")
                continue
        
        return plan
    
    def _customize_template(self, template_plan: ResearchPlan, goal: str) -> ResearchPlan:
        """Customize a template plan for the specific goal."""
        customized_plan = ResearchPlan(goal, template_plan.complexity)
        
        for step in template_plan.steps:
            # Customize parameters based on goal
            customized_params = step.parameters.copy()
            
            # Replace generic queries with goal-specific ones
            if 'query' in customized_params:
                customized_params['query'] = customized_params['query'].replace('{goal}', goal)
            
            # Create customized step
            customized_step = ResearchStep(
                action=step.action,
                tool=step.tool,
                parameters=customized_params,
                description=step.description.replace('{goal}', goal),
                expected_output=step.expected_output,
                priority=step.priority,
                estimated_time=step.estimated_time
            )
            
            customized_plan.steps.append(customized_step)
        
        logger.info(f"Customized template plan for: {goal}")
        return customized_plan
    
    def _optimize_plan(self, plan: ResearchPlan) -> ResearchPlan:
        """Optimize the research plan for better efficiency."""
        logger.debug("Optimizing research plan")
        
        # Group similar search actions
        search_steps = []
        scraping_steps = []
        processing_steps = []
        other_steps = []
        
        for step in plan.steps:
            if 'search' in step.action:
                search_steps.append(step)
            elif 'scrape' in step.action:
                scraping_steps.append(step)
            elif step.tool == 'data_processor':
                processing_steps.append(step)
            else:
                other_steps.append(step)
        
        # Reorder for optimal execution
        optimized_steps = []
        optimized_steps.extend(search_steps)
        optimized_steps.extend(other_steps)
        optimized_steps.extend(scraping_steps)
        optimized_steps.extend(processing_steps)
        
        # Update priorities
        for i, step in enumerate(optimized_steps):
            step.priority = i + 1
        
        plan.steps = optimized_steps
        logger.debug(f"Plan optimized: {len(plan.steps)} steps reordered")
        
        return plan
    
    def _create_fallback_plan(self, goal: str, complexity: str) -> ResearchPlan:
        """Create a simple fallback plan."""
        logger.info("Creating fallback research plan")
        
        complexity_params = self._get_complexity_parameters(complexity)
        max_results = complexity_params['sources_per_topic']
        
        plan = ResearchPlan(goal, complexity)
        
        # Step 1: Initial web search
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": goal, "max_results": max_results},
            description=f"Search for information about: {goal}",
            expected_output="List of relevant web sources"
        )
        
        # Step 2: Scrape found sources
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 5},
            description="Extract content from found sources",
            expected_output="Raw content from web sources"
        )
        
        # Step 3: Clean and process data (if complexity requires it)
        if complexity != 'simple':
            plan.add_step(
                action="clean_data",
                tool="data_processor",
                parameters={"data": "scraped_content", "strictness": "medium"},
                description="Clean and organize the collected data",
                expected_output="Cleaned and structured data"
            )
        
        return plan
    
    async def validate(self) -> bool:
        """Validate that the plan generator is ready."""
        try:
            # Test AI client connection
            if not self.ai_client.is_connected():
                logger.error("AI client not connected")
                return False
            
            # Test plan generation with simple goal
            test_plan = await self.generate_plan("test research topic", "simple")
            
            if not test_plan.validate():
                logger.error("Test plan generation failed validation")
                return False
            
            logger.debug("Plan generator validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Plan generator validation failed: {e}")
            return False
