"""Enhanced web scraping utilities for research execution."""

import asyncio
import random
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse, quote_plus
import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class WebScraper:
    """Enhanced web scraper with multiple search engines and better error handling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Configuration
        self.max_retries = config.get('scraping.max_retries', 3)
        self.timeout = config.get('scraping.timeout', 30)
        self.delay = config.get('scraping.request_delay', 1.0)
        self.concurrent_limit = config.get('scraping.concurrent_requests', 10)
        
        # User agents
        self.user_agents = config.get('scraping.user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ])
    
    def search_web(self, query: str, max_results: int = 10, time_filter: str = "") -> List[Dict[str, Any]]:
        """Search the web using multiple search engines."""
        logger.info(f"Searching web for: {query} (max_results: {max_results})")
        
        # Try different search engines
        search_engines = [
            self._search_duckduckgo,
            self._search_bing,
            self._search_searx
        ]
        
        all_results = []
        
        for search_engine in search_engines:
            try:
                results = search_engine(query, max_results, time_filter)
                if results:
                    all_results.extend(results)
                    logger.info(f"Found {len(results)} results from {search_engine.__name__}")
                    
                    # If we have enough results, stop
                    if len(all_results) >= max_results:
                        break
                        
            except Exception as e:
                logger.warning(f"Search engine {search_engine.__name__} failed: {e}")
                continue
        
        # Remove duplicates and limit results
        unique_results = self._deduplicate_results(all_results)
        final_results = unique_results[:max_results]
        
        logger.info(f"Final search results: {len(final_results)} unique URLs")
        return final_results
    
    def _search_duckduckgo(self, query: str, max_results: int, time_filter: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        encoded_query = quote_plus(query)
        search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
        
        if time_filter:
            # DuckDuckGo time filters: d (day), w (week), m (month), y (year)
            time_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
            if time_filter in time_map:
                search_url += f"&df={time_map[time_filter]}"
        
        headers = self._get_headers()
        
        try:
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            for result in soup.find_all('a', class_='result__a', limit=max_results):
                href = result.get('href')
                title = result.get_text().strip()
                
                if href and title and href.startswith('http'):
                    results.append({
                        'url': href,
                        'title': title,
                        'source': 'duckduckgo'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _search_bing(self, query: str, max_results: int, time_filter: str) -> List[Dict[str, Any]]:
        """Search using Bing."""
        encoded_query = quote_plus(query)
        search_url = f"https://www.bing.com/search?q={encoded_query}"
        
        headers = self._get_headers()
        
        try:
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            for result in soup.find_all('h2', limit=max_results):
                link = result.find('a')
                if link:
                    href = link.get('href')
                    title = link.get_text().strip()
                    
                    if href and title and href.startswith('http'):
                        results.append({
                            'url': href,
                            'title': title,
                            'source': 'bing'
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []
    
    def _search_searx(self, query: str, max_results: int, time_filter: str) -> List[Dict[str, Any]]:
        """Search using SearX instance."""
        # Public SearX instances
        searx_instances = [
            "https://searx.be",
            "https://search.privacytools.io",
            "https://searx.xyz"
        ]
        
        for instance in searx_instances:
            try:
                encoded_query = quote_plus(query)
                search_url = f"{instance}/search?q={encoded_query}&format=json"
                
                headers = self._get_headers()
                response = self.session.get(search_url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                results = []
                
                for result in data.get('results', [])[:max_results]:
                    url = result.get('url')
                    title = result.get('title')
                    
                    if url and title:
                        results.append({
                            'url': url,
                            'title': title,
                            'source': 'searx'
                        })
                
                if results:
                    return results
                    
            except Exception as e:
                logger.debug(f"SearX instance {instance} failed: {e}")
                continue
        
        return []
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate URLs from search results."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently with rate limiting."""
        logger.info(f"Scraping {len(urls)} URLs concurrently")
        
        if not urls:
            return []
        
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def scrape_one(url: str) -> Dict[str, Any]:
            async with semaphore:
                # Add random delay to avoid rate limiting
                await asyncio.sleep(random.uniform(0.5, 1.5))
                return await asyncio.to_thread(self.scrape_url, url)
        
        tasks = [scrape_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                logger.error(f"Scraping URL {urls[i] if i < len(urls) else 'unknown'} failed: {result}")
        
        successful = len(valid_results)
        logger.info(f"Successfully scraped {successful}/{len(urls)} URLs")
        
        return valid_results
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape a single URL with enhanced error handling."""
        logger.debug(f"Scraping URL: {url}")
        
        for attempt in range(self.max_retries):
            try:
                headers = self._get_headers()
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Parse content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title_elem = soup.find('title')
                title = title_elem.get_text().strip() if title_elem else ""
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                    element.decompose()
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                # Extract metadata
                metadata = self._extract_metadata(soup, response)
                
                # Extract links
                links = self._extract_links(soup, url)
                
                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'links': links,
                    'metadata': metadata,
                    'status': 'success',
                    'word_count': len(content.split()) if content else 0,
                    'source_type': 'web'
                }
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return self._create_error_result(url, str(e))
            
            except Exception as e:
                logger.error(f"Unexpected error scraping {url}: {e}")
                return self._create_error_result(url, str(e))
        
        return self._create_error_result(url, "Max retries exceeded")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests."""
        user_agent = random.choice(self.user_agents) if self.user_agents else self.ua.random
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from parsed HTML."""
        # Try to find main content areas
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '.post-content',
            '.entry-content',
            '#content',
            '#main'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content.get_text(separator=' ', strip=True)
        
        # Fallback: get all text from body
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        # Final fallback: all text
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_metadata(self, soup: BeautifulSoup, response: requests.Response) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {
            'domain': urlparse(response.url).netloc,
            'content_type': response.headers.get('content-type', ''),
            'status_code': response.status_code,
            'final_url': response.url
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from the page."""
        links = []
        
        for a in soup.find_all('a', href=True, limit=50):
            href = a.get('href')
            text = a.get_text().strip()
            
            if href and text:
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                
                links.append({
                    'text': text,
                    'href': absolute_url
                })
        
        return links
    
    def _create_error_result(self, url: str, error: str) -> Dict[str, Any]:
        """Create error result for failed scraping."""
        return {
            'url': url,
            'title': '',
            'content': '',
            'links': [],
            'metadata': {},
            'status': 'failed',
            'error': error,
            'word_count': 0,
            'source_type': 'web'
        }
