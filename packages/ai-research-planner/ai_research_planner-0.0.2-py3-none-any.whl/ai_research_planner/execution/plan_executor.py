"""Executes research plans by performing web searches, scraping, and cleaning."""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from ai_research_planner.utils.logger import get_logger
from ai_research_planner.execution.web_scraper import WebScraper
from ai_research_planner.execution.data_cleaner import DataCleaner
from ai_research_planner.models import ResearchPlan, ResearchResults, DataItem

logger = get_logger(__name__)


class PlanExecutor:
    """Executes research plans step by step."""
    
    def __init__(self, ai_client, config):
        self.ai_client = ai_client
        self.config = config
        self.web_scraper = WebScraper(config)
        self.data_cleaner = DataCleaner(config)
        
        # Execution settings
        self.save_intermediate = config.get('storage.save_intermediate_results', True)
        self.max_retries = config.get('scraping.max_retries', 3)
    
    async def execute(self, plan: ResearchPlan) -> ResearchResults:
        """Execute the complete research plan."""
        logger.info(f"Executing research plan: {plan.goal}")
        logger.info(f"Plan complexity: {plan.complexity}")
        logger.info(f"Total steps: {len(plan.steps)}")
        
        results = ResearchResults(plan.id, plan.goal)
        all_scraped_data = []
        
        for i, step in enumerate(plan.steps, 1):
            logger.info(f"Executing step {i}/{len(plan.steps)}: {step.description}")
            
            try:
                step_data = await self._execute_step_with_retry(step, i)
                
                if step_data:
                    # Convert to DataItem objects properly
                    if isinstance(step_data, list):
                        data_items = []
                        for item in step_data:
                            data_item = self._convert_to_data_item(item)
                            if data_item:
                                data_items.append(data_item)
                        
                        all_scraped_data.extend(data_items)
                        results.add_raw_data(data_items)
                    else:
                        # Single item
                        data_item = self._convert_to_data_item(step_data)
                        if data_item:
                            all_scraped_data.append(data_item)
                            results.add_raw_data([data_item])
                    
                    results.add_execution_log(
                        step.description, 
                        "success", 
                        {
                            "data_count": len(step_data) if isinstance(step_data, list) else 1,
                            "step_number": i,
                            "tool_used": step.tool,
                            "action": step.action
                        }
                    )
                    logger.info(f"Step {i} completed successfully: {len(step_data) if isinstance(step_data, list) else 1} items")
                else:
                    results.add_execution_log(
                        step.description, 
                        "failed", 
                        {
                            "reason": "No data returned",
                            "step_number": i,
                            "tool_used": step.tool,
                            "action": step.action
                        }
                    )
                    logger.warning(f"Step {i} returned no data")
                
            except Exception as e:
                logger.error(f"Error executing step {i} ({step.description}): {e}")
                results.add_execution_log(
                    step.description, 
                    "failed", 
                    {
                        "error": str(e),
                        "step_number": i,
                        "tool_used": step.tool,
                        "action": step.action
                    }
                )
            
            # Add delay between steps
            if i < len(plan.steps):
                await asyncio.sleep(1.0)
        
        # Clean data if enabled and we have data
        if all_scraped_data:
            await self._clean_and_finalize_data(results, all_scraped_data)
        else:
            logger.warning("No data collected during plan execution")
            results.set_cleaned_data([])
        
        logger.info(f"Plan execution completed. Total items: {len(results.raw_data)}, Cleaned items: {len(results.cleaned_data)}")
        return results
    
    def _convert_to_data_item(self, item: Any) -> DataItem:
        """Convert various item formats to DataItem."""
        if isinstance(item, DataItem):
            return item
        elif isinstance(item, dict):
            # Create clean item with all required fields
            clean_item = {
                'url': item.get('url', ''),
                'title': item.get('title', ''),
                'content': item.get('content', ''),
                'source_type': item.get('source_type', 'web'),
                'timestamp': item.get('timestamp', ''),
                'metadata': item.get('metadata', {}),
                'links': item.get('links', []),
                'status': item.get('status', 'success'),
                'word_count': item.get('word_count', 0),
                'error': item.get('error', None)
            }
            try:
                return DataItem(**clean_item)
            except Exception as e:
                logger.error(f"Failed to convert item to DataItem: {e}")
                return None
        else:
            logger.warning(f"Unknown item type: {type(item)}")
            return None
    
    async def _execute_step_with_retry(self, step, step_number: int):
        """Execute a step with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retrying step {step_number}, attempt {attempt + 1}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                return await self._execute_single_step(step)
                
            except Exception as e:
                last_error = e
                logger.warning(f"Step {step_number} attempt {attempt + 1} failed: {e}")
        
        # All retries failed
        logger.error(f"Step {step_number} failed after {self.max_retries} attempts: {last_error}")
        raise last_error
    
    async def _execute_single_step(self, step):
        """Execute a single step based on its tool and action."""
        
        if step.tool in ["web_searcher", "web_scraper"]:
            return await self._execute_web_step(step)
        elif step.tool == "data_processor":
            return await self._execute_data_processing_step(step)
        elif step.tool == "data_analyzer":
            return await self._execute_data_analysis_step(step)
        elif step.tool == "url_navigator":
            return await self._execute_url_navigation_step(step)
        else:
            logger.warning(f"Unknown tool: {step.tool}, treating as web search")
            return await self._execute_web_step(step)
    
    async def _execute_web_step(self, step):
        """Execute web search and scraping steps."""
        action = step.action
        params = step.parameters
        
        if action in ["search_web", "search_academic", "search_news"]:
            query = params.get("query", "")
            max_results = params.get("max_results", 10)
            time_filter = params.get("time_filter", "")
            
            if not query:
                logger.warning("No query provided for web search")
                return []
            
            # Perform web search
            search_results = self.web_scraper.search_web(query, max_results, time_filter)
            
            if not search_results:
                logger.warning(f"No search results found for query: {query}")
                return []
            
            # Extract URLs and scrape content
            urls = [result.get("url") for result in search_results if result.get("url") and result.get("url").startswith('http')]
            
            if urls:
                scraped_data = await self.web_scraper.scrape_multiple_urls(urls[:max_results])
                return scraped_data
            else:
                logger.warning("No valid URLs found in search results")
                return []
                
        elif action in ["scrape_url", "scrape_urls", "scrape_multiple_urls"]:
            if action == "scrape_url":
                url = params.get("url", "")
                if url and url.startswith('http'):
                    result = self.web_scraper.scrape_url(url)
                    return [result] if result else []
                else:
                    logger.warning(f"Invalid URL: {url}")
                    return []
            else:
                urls = params.get("urls", [])
                source = params.get("source", "")
                
                if source == "search_results":
                    # This step depends on previous search results
                    logger.info("Scraping from search results - skipping for now")
                    return []
                elif urls:
                    # Validate URLs before scraping
                    valid_urls = [url for url in urls if isinstance(url, str) and url.startswith('http')]
                    if valid_urls:
                        return await self.web_scraper.scrape_multiple_urls(valid_urls)
                    else:
                        logger.warning("No valid URLs provided for scraping")
                        return []
        
        return []
    
    async def _execute_data_processing_step(self, step):
        """Execute data processing steps."""
        action = step.action
        params = step.parameters
        
        if action == "clean_data":
            # This would typically work on previously collected data
            # For now, just return empty
            logger.info("Data cleaning step - handled in post-processing")
            return []
        elif action == "extract_keywords":
            # Extract keywords from collected content
            logger.info("Keyword extraction step - handled in post-processing")
            return []
        elif action == "summarize_content":
            # Summarize collected content
            logger.info("Content summarization step - handled in post-processing")
            return []
        
        return []
    
    async def _execute_data_analysis_step(self, step):
        """Execute data analysis steps."""
        action = step.action
        params = step.parameters
        
        if action == "analyze_trends":
            logger.info("Trend analysis step - handled in post-processing")
            return []
        elif action == "compare_sources":
            logger.info("Source comparison step - handled in post-processing")
            return []
        elif action == "validate_facts":
            logger.info("Fact validation step - handled in post-processing")
            return []
        
        return []
    
    async def _execute_url_navigation_step(self, step):
        """Execute URL navigation steps."""
        action = step.action
        params = step.parameters
        
        if action == "get_links":
            url = params.get("url", "")
            if url and url.startswith('http'):
                result = self.web_scraper.scrape_url(url)
                return [result] if result else []
            else:
                logger.warning(f"Invalid URL for link extraction: {url}")
                return []
        elif action == "follow_links":
            base_url = params.get("base_url", "")
            pattern = params.get("pattern", "")
            max_links = params.get("max_links", 5)
            
            if base_url and base_url.startswith('http'):
                # Get links from base URL and follow matching ones
                base_result = self.web_scraper.scrape_url(base_url)
                if base_result and base_result.get("links"):
                    matching_urls = []
                    for link in base_result["links"]:
                        href = link.get("href", "")
                        if href.startswith('http') and pattern.lower() in href.lower():
                            matching_urls.append(href)
                            if len(matching_urls) >= max_links:
                                break
                    
                    if matching_urls:
                        return await self.web_scraper.scrape_multiple_urls(matching_urls)
                else:
                    logger.info("No links found in base URL")
            else:
                logger.warning(f"Invalid base URL: {base_url}")
        
        return []
    
    async def _clean_and_finalize_data(self, results: ResearchResults, all_data: List[DataItem]):
        """Clean data and finalize results."""
        
        cleaning_enabled = self.config.get('research.data_cleaning.enabled', True)
        min_retention = self.config.get('research.data_cleaning.min_data_retention', 0.7)
        
        if cleaning_enabled and all_data:
            logger.info(f"Cleaning {len(all_data)} data items")
            
            # Convert DataItem objects to dicts for cleaning
            data_dicts = []
            for item in all_data:
                try:
                    data_dict = {
                        'url': item.url,
                        'title': item.title,
                        'content': item.content,
                        'source_type': item.source_type,
                        'timestamp': item.timestamp,
                        'metadata': item.metadata,
                        'links': item.links,
                        'status': item.status,
                        'word_count': item.word_count,
                        'error': item.error
                    }
                    data_dicts.append(data_dict)
                except Exception as e:
                    logger.warning(f"Failed to convert DataItem to dict: {e}")
                    continue
            
            if data_dicts:
                cleaned_dicts = self.data_cleaner.clean_data(data_dicts)
                
                # Check retention rate
                retention_rate = len(cleaned_dicts) / len(data_dicts) if data_dicts else 0
                
                if retention_rate >= min_retention:
                    # Convert back to DataItem objects
                    cleaned_items = []
                    for item_dict in cleaned_dicts:
                        try:
                            cleaned_item = DataItem(**item_dict)
                            cleaned_items.append(cleaned_item)
                        except Exception as e:
                            logger.warning(f"Failed to convert cleaned dict to DataItem: {e}")
                            continue
                    
                    results.set_cleaned_data(cleaned_items)
                    logger.info(f"Data cleaning completed. Retained {len(cleaned_items)}/{len(all_data)} items ({retention_rate:.1%})")
                else:
                    # Skip cleaning - too much data would be lost
                    results.set_cleaned_data(all_data)
                    logger.warning(f"Data cleaning skipped - would remove {1-retention_rate:.1%} of data")
            else:
                results.set_cleaned_data(all_data)
                logger.warning("No valid data for cleaning - using raw data")
        else:
            # No cleaning
            results.set_cleaned_data(all_data)
            logger.info("Data cleaning disabled - using raw data")
    
    def validate(self) -> bool:
        """Validate that the executor is ready."""
        try:
            # Check if web scraper is configured
            if not self.web_scraper:
                return False
            
            # Check if data cleaner is configured
            if not self.data_cleaner:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Executor validation failed: {e}")
            return False
