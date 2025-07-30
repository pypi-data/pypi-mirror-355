"""Pre-built research plan templates for common research patterns."""

from typing import Dict, Optional, List
from ai_research_planner.models import ResearchPlan, ResearchStep
from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class PlanTemplates:
    """Manages pre-built research plan templates."""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, ResearchPlan]:
        """Load all available templates."""
        templates = {}
        
        # Technology Research Template
        templates['technology'] = self._create_technology_template()
        
        # Market Research Template
        templates['market'] = self._create_market_template()
        
        # Academic Research Template
        templates['academic'] = self._create_academic_template()
        
        # News Research Template
        templates['news'] = self._create_news_template()
        
        # Competitive Analysis Template
        templates['competitive'] = self._create_competitive_template()
        
        # Trend Analysis Template
        templates['trends'] = self._create_trends_template()
        
        logger.info(f"Loaded {len(templates)} research plan templates")
        return templates
    
    def get_template_for_goal(self, goal: str) -> Optional[ResearchPlan]:
        """Get the most appropriate template for a research goal."""
        goal_lower = goal.lower()
        
        # Technology keywords
        tech_keywords = ['ai', 'artificial intelligence', 'machine learning', 'technology', 
                        'software', 'programming', 'development', 'tech', 'innovation',
                        'digital', 'computer', 'automation', 'blockchain', 'cloud']
        
        # Market keywords
        market_keywords = ['market', 'industry', 'business', 'economy', 'financial',
                          'revenue', 'profit', 'sales', 'commercial', 'sector',
                          'investment', 'startup', 'company', 'corporation']
        
        # Academic keywords
        academic_keywords = ['research', 'study', 'academic', 'scientific', 'scholarly',
                           'paper', 'journal', 'peer review', 'methodology', 'analysis',
                           'experiment', 'theory', 'hypothesis']
        
        # News keywords
        news_keywords = ['news', 'current', 'recent', 'latest', 'breaking', 'update',
                        'development', 'event', 'announcement', 'happening', 'today']
        
        # Competitive keywords
        competitive_keywords = ['competitor', 'competitive', 'comparison', 'vs', 'versus',
                              'compare', 'alternative', 'benchmark', 'rival']
        
        # Trend keywords
        trend_keywords = ['trend', 'trending', 'future', 'prediction', 'forecast',
                         'outlook', 'emerging', 'growth', 'decline', 'pattern']
        
        # Check goal against keywords
        if any(keyword in goal_lower for keyword in tech_keywords):
            return self.templates.get('technology')
        elif any(keyword in goal_lower for keyword in market_keywords):
            return self.templates.get('market')
        elif any(keyword in goal_lower for keyword in academic_keywords):
            return self.templates.get('academic')
        elif any(keyword in goal_lower for keyword in news_keywords):
            return self.templates.get('news')
        elif any(keyword in goal_lower for keyword in competitive_keywords):
            return self.templates.get('competitive')
        elif any(keyword in goal_lower for keyword in trend_keywords):
            return self.templates.get('trends')
        
        # Default to technology template
        return self.templates.get('technology')
    
    def _create_technology_template(self) -> ResearchPlan:
        """Create technology research template."""
        plan = ResearchPlan("{goal}", "standard")
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} technology overview", "max_results": 10},
            description="Search for technology overview and general information",
            expected_output="General technology information"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} latest developments 2024 2025", "max_results": 8},
            description="Search for recent developments and updates",
            expected_output="Recent technology developments"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} use cases applications", "max_results": 8},
            description="Search for practical applications and use cases",
            expected_output="Technology applications and use cases"
        )
        
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 5},
            description="Extract content from found technology sources",
            expected_output="Detailed technology content"
        )
        
        plan.add_step(
            action="clean_data",
            tool="data_processor",
            parameters={"data": "scraped_content", "strictness": "medium"},
            description="Clean and organize technology data",
            expected_output="Cleaned technology information"
        )
        
        return plan
    
    def _create_market_template(self) -> ResearchPlan:
        """Create market research template."""
        plan = ResearchPlan("{goal}", "standard")
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} market size analysis", "max_results": 10},
            description="Search for market size and analysis",
            expected_output="Market size and analysis data"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} key players competitors", "max_results": 8},
            description="Search for key market players and competitors",
            expected_output="Competitor and player information"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} market trends forecast", "max_results": 8},
            description="Search for market trends and forecasts",
            expected_output="Market trends and predictions"
        )
        
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 5},
            description="Extract content from market research sources",
            expected_output="Detailed market content"
        )
        
        plan.add_step(
            action="clean_data",
            tool="data_processor",
            parameters={"data": "scraped_content", "strictness": "medium"},
            description="Clean and organize market data",
            expected_output="Cleaned market information"
        )
        
        return plan
    
    def _create_academic_template(self) -> ResearchPlan:
        """Create academic research template."""
        plan = ResearchPlan("{goal}", "deep")
        
        plan.add_step(
            action="search_academic",
            tool="web_searcher",
            parameters={"query": "{goal} academic papers", "max_results": 15},
            description="Search for academic papers and scholarly articles",
            expected_output="Academic paper citations and abstracts"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} research methodology", "max_results": 8},
            description="Search for research methodologies and approaches",
            expected_output="Research methodology information"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} recent studies findings", "max_results": 10},
            description="Search for recent studies and findings",
            expected_output="Recent research findings"
        )
        
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 3},
            description="Extract content from academic sources",
            expected_output="Detailed academic content"
        )
        
        plan.add_step(
            action="validate_facts",
            tool="data_analyzer",
            parameters={"data": "scraped_content", "cross_reference": True},
            description="Validate facts and cross-reference information",
            expected_output="Validated academic information"
        )
        
        plan.add_step(
            action="clean_data",
            tool="data_processor",
            parameters={"data": "validated_content", "strictness": "high"},
            description="Clean and organize academic data",
            expected_output="Cleaned academic information"
        )
        
        return plan
    
    def _create_news_template(self) -> ResearchPlan:
        """Create news research template."""
        plan = ResearchPlan("{goal}", "simple")
        
        plan.add_step(
            action="search_news",
            tool="web_searcher",
            parameters={"query": "{goal} latest news", "max_results": 15, "time_filter": "week"},
            description="Search for latest news articles",
            expected_output="Recent news articles"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} breaking news updates", "max_results": 10},
            description="Search for breaking news and updates",
            expected_output="Breaking news and updates"
        )
        
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 8},
            description="Extract content from news sources",
            expected_output="Detailed news content"
        )
        
        plan.add_step(
            action="clean_data",
            tool="data_processor",
            parameters={"data": "scraped_content", "strictness": "low"},
            description="Clean and organize news data",
            expected_output="Cleaned news information"
        )
        
        return plan
    
    def _create_competitive_template(self) -> ResearchPlan:
        """Create competitive analysis template."""
        plan = ResearchPlan("{goal}", "standard")
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} competitive analysis", "max_results": 10},
            description="Search for competitive analysis reports",
            expected_output="Competitive analysis information"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} market share comparison", "max_results": 8},
            description="Search for market share and comparison data",
            expected_output="Market share comparison data"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} pricing features comparison", "max_results": 8},
            description="Search for pricing and feature comparisons",
            expected_output="Pricing and feature comparison data"
        )
        
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 5},
            description="Extract content from competitive sources",
            expected_output="Detailed competitive content"
        )
        
        plan.add_step(
            action="compare_sources",
            tool="data_analyzer",
            parameters={"data": "scraped_content", "comparison_fields": ["features", "pricing", "market_share"]},
            description="Compare and analyze competitive data",
            expected_output="Comparative analysis results"
        )
        
        plan.add_step(
            action="clean_data",
            tool="data_processor",
            parameters={"data": "analysis_results", "strictness": "medium"},
            description="Clean and organize competitive analysis",
            expected_output="Cleaned competitive intelligence"
        )
        
        return plan
    
    def _create_trends_template(self) -> ResearchPlan:
        """Create trend analysis template."""
        plan = ResearchPlan("{goal}", "deep")
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} trends 2024 2025", "max_results": 12},
            description="Search for current and future trends",
            expected_output="Current and future trend information"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} market forecast predictions", "max_results": 10},
            description="Search for market forecasts and predictions",
            expected_output="Market forecast and prediction data"
        )
        
        plan.add_step(
            action="search_web",
            tool="web_searcher",
            parameters={"query": "{goal} growth patterns statistics", "max_results": 8},
            description="Search for growth patterns and statistics",
            expected_output="Growth pattern and statistical data"
        )
        
        plan.add_step(
            action="scrape_multiple_urls",
            tool="web_scraper",
            parameters={"source": "search_results", "max_concurrent": 5},
            description="Extract content from trend analysis sources",
            expected_output="Detailed trend content"
        )
        
        plan.add_step(
            action="analyze_trends",
            tool="data_analyzer",
            parameters={"data": "scraped_content", "time_period": "5_years"},
            description="Analyze trends and patterns in the data",
            expected_output="Trend analysis results"
        )
        
        plan.add_step(
            action="clean_data",
            tool="data_processor",
            parameters={"data": "trend_analysis", "strictness": "medium"},
            description="Clean and organize trend analysis",
            expected_output="Cleaned trend intelligence"
        )
        
        return plan
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def get_template(self, template_name: str) -> Optional[ResearchPlan]:
        """Get a specific template by name."""
        return self.templates.get(template_name)
