"""Enhanced data cleaning utilities for research execution."""

import re
from typing import List, Dict, Any
from urllib.parse import urlparse

from ai_research_planner.utils.config import Config
from ai_research_planner.utils.logger import get_logger

logger = get_logger(__name__)


class DataCleaner:
    """Cleans and processes scraped research data."""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Cleaning settings
        self.strictness = config.get('research.data_cleaning.strictness', 'medium')
        self.min_content_length = self._get_min_content_length()
        self.max_content_length = 50000  # Prevent extremely long content
        
        # Unwanted patterns
        self.noise_patterns = [
            r'cookie\s+policy',
            r'privacy\s+policy',
            r'terms\s+of\s+service',
            r'subscribe\s+to\s+newsletter',
            r'follow\s+us\s+on',
            r'share\s+this\s+article',
            r'advertisement',
            r'sponsored\s+content'
        ]
        
        # Quality indicators
        self.quality_keywords = [
            'research', 'study', 'analysis', 'report', 'findings',
            'data', 'statistics', 'methodology', 'results', 'conclusion'
        ]
        
        # Domains to prioritize or filter
        self.trusted_domains = [
            'edu', 'gov', 'org', 'reuters.com', 'bbc.com', 'nature.com',
            'science.org', 'ieee.org', 'acm.org', 'arxiv.org'
        ]
        
        self.blocked_domains = [
            'pinterest.com', 'instagram.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'youtube.com', 'tiktok.com'
        ]
    
    def clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and filter the scraped data."""
        logger.info(f"Cleaning {len(data)} data items with {self.strictness} strictness")
        
        if not data:
            return []
        
        cleaned_data = []
        
        for item in data:
            try:
                # Skip failed scrapes
                if item.get('status') == 'failed':
                    continue
                
                # Clean individual item
                cleaned_item = self._clean_single_item(item)
                
                if cleaned_item and self._is_quality_content(cleaned_item):
                    cleaned_data.append(cleaned_item)
                    
            except Exception as e:
                logger.warning(f"Error cleaning item {item.get('url', 'unknown')}: {e}")
                continue
        
        # Sort by quality score
        cleaned_data = self._rank_by_quality(cleaned_data)
        
        logger.info(f"Cleaned data count: {len(cleaned_data)}/{len(data)} items retained")
        return cleaned_data
    
    def _clean_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single data item."""
        cleaned_item = item.copy()
        
        # Clean URL
        url = item.get('url', '')
        if not self._is_valid_url(url):
            return None
        
        # Clean title
        title = self._clean_text(item.get('title', ''))
        if not title or len(title) < 10:
            return None
        
        # Clean content
        content = self._clean_content(item.get('content', ''))
        if not content or len(content) < self.min_content_length:
            return None
        
        # Update cleaned item
        cleaned_item.update({
            'title': title,
            'content': content,
            'word_count': len(content.split()),
            'quality_score': self._calculate_quality_score(title, content, url)
        })
        
        return cleaned_item
    
    def _clean_content(self, content: str) -> str:
        """Clean the content text."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove noise patterns
        for pattern in self.noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove very short lines (likely navigation/menu items)
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 20]
        content = ' '.join(cleaned_lines)
        
        # Remove repeated sentences
        content = self._remove_repeated_content(content)
        
        # Limit length
        if len(content) > self.max_content_length:
            content = content[:self.max_content_length] + "..."
        
        return content.strip()
    
    def _clean_text(self, text: str) -> str:
        """Clean general text (titles, etc.)."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise
        text = re.sub(r'^\s*[-|•]\s*', '', text)  # Remove leading bullets
        text = re.sub(r'\s*[-|•]\s*$', '', text)  # Remove trailing bullets
        
        return text.strip()
    
    def _remove_repeated_content(self, content: str) -> str:
        """Remove repeated sentences or paragraphs."""
        sentences = content.split('.')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:
                # Use first 50 characters as key to detect near-duplicates
                key = sentence[:50].lower()
                if key not in seen:
                    seen.add(key)
                    unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not blocked."""
        if not url or not url.startswith('http'):
            return False
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check blocked domains
            for blocked in self.blocked_domains:
                if blocked in domain:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _is_quality_content(self, item: Dict[str, Any]) -> bool:
        """Determine if content meets quality standards."""
        content = item.get('content', '')
        title = item.get('title', '')
        url = item.get('url', '')
        
        # Length checks based on strictness
        min_length = self.min_content_length
        
        if len(content) < min_length:
            return False
        
        # Check for quality indicators
        quality_score = item.get('quality_score', 0)
        
        if self.strictness == 'low':
            return quality_score > 0.2
        elif self.strictness == 'medium':
            return quality_score > 0.4
        elif self.strictness == 'high':
            return quality_score > 0.6
        
        return True
    
    def _calculate_quality_score(self, title: str, content: str, url: str) -> float:
        """Calculate quality score for content."""
        score = 0.0
        
        # Domain trust score
        domain_score = self._get_domain_score(url)
        score += domain_score * 0.3
        
        # Content quality score
        content_score = self._get_content_quality_score(content)
        score += content_score * 0.5
        
        # Title quality score
        title_score = self._get_title_quality_score(title)
        score += title_score * 0.2
        
        return min(score, 1.0)
    
    def _get_domain_score(self, url: str) -> float:
        """Get domain trustworthiness score."""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check trusted domains
            for trusted in self.trusted_domains:
                if trusted in domain:
                    return 1.0
            
            # Check TLD
            if domain.endswith('.edu') or domain.endswith('.gov'):
                return 0.9
            elif domain.endswith('.org'):
                return 0.7
            elif domain.endswith('.com'):
                return 0.5
            
            return 0.3
            
        except Exception:
            return 0.1
    
    def _get_content_quality_score(self, content: str) -> float:
        """Get content quality score based on various factors."""
        if not content:
            return 0.0
        
        score = 0.0
        content_lower = content.lower()
        
        # Length bonus
        word_count = len(content.split())
        if word_count > 100:
            score += 0.2
        if word_count > 500:
            score += 0.2
        if word_count > 1000:
            score += 0.1
        
        # Quality keyword presence
        quality_matches = sum(1 for keyword in self.quality_keywords if keyword in content_lower)
        score += min(quality_matches / len(self.quality_keywords), 0.3)
        
        # Sentence structure (approximation)
        sentences = content.count('.')
        if sentences > 5:
            score += 0.1
        
        # Paragraph structure
        paragraphs = content.count('\n\n')
        if paragraphs > 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_title_quality_score(self, title: str) -> float:
        """Get title quality score."""
        if not title:
            return 0.0
        
        score = 0.0
        title_lower = title.lower()
        
        # Length check
        if 10 <= len(title) <= 100:
            score += 0.3
        
        # Quality indicators in title
        for keyword in self.quality_keywords:
            if keyword in title_lower:
                score += 0.2
                break
        
        # Avoid clickbait patterns
        clickbait_patterns = [
            r'\d+\s+things', r'you\s+won\'t\s+believe', r'shocking',
            r'amazing', r'incredible', r'unbelievable'
        ]
        
        for pattern in clickbait_patterns:
            if re.search(pattern, title_lower):
                score -= 0.2
                break
        
        return max(0.0, min(score, 1.0))
    
    def _rank_by_quality(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank data items by quality score."""
        return sorted(data, key=lambda x: x.get('quality_score', 0), reverse=True)
    
    def _get_min_content_length(self) -> int:
        """Get minimum content length based on strictness."""
        if self.strictness == 'low':
            return 100
        elif self.strictness == 'medium':
            return 200
        elif self.strictness == 'high':
            return 500
        return 200
