import os
import requests
import json
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")  # Update to your Gemini API key
        self.model = "gemini-pro"  # Gemini's free model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.timeout = 30  # seconds

    def _make_api_request(self, payload: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Helper method to make API requests to Gemini"""
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json(), None
                
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if isinstance(e, requests.exceptions.HTTPError):
                error_msg += f" (Status Code: {response.status_code})"
                if response.status_code == 401:
                    error_msg += " - Invalid API Key"
                elif response.status_code == 429:
                    error_msg += " - Rate Limit Exceeded"
            return None, error_msg

    def generate_news_articles(self, count: int = 5) -> Tuple[List[Dict], Optional[str]]:
        """Generate sample news articles using Gemini"""
        prompt = f"""Generate {count} diverse news articles in JSON format with:
        - title (string)
        - description (string)
        - category (Technology/Business/Science)
        - source_name (string)
        - relevance_score (0-1)
        - latitude/longitude (float)
        Example: {json.dumps({
            "title": "Sample",
            "description": "Sample description",
            "category": "Technology",
            "source_name": "NewsSource",
            "relevance_score": 0.9,
            "latitude": 37.7749,
            "longitude": -122.4194
        })}"""
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        }
        
        result, error = self._make_api_request(payload)
        if error:
            return self._get_fallback_articles(count), error
            
        try:
            # Gemini returns JSON in a different structure
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            articles = json.loads(response_text)
            if not isinstance(articles, list):
                raise ValueError("API didn't return a list of articles")
            return articles, None
        except Exception as e:
            return self._get_fallback_articles(count), f"Response parsing failed: {str(e)}"

    def generate_summary(self, text: str, max_length: int = 200) -> Tuple[str, Optional[str]]:
        """Generate summary using Gemini"""
        prompt = f"""Summarize this in 1-2 sentences under {max_length} characters:
        {text}"""
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 100,
                "temperature": 0.3
            }
        }
        
        result, error = self._make_api_request(payload)
        if error:
            fallback = text[:max_length].rsplit(' ', 1)[0] + "..." if len(text) > max_length else text
            return fallback, error
            
        try:
            summary = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            return summary, None
        except Exception as e:
            fallback = text[:max_length].rsplit(' ', 1)[0] + "..." if len(text) > max_length else text
            return fallback, f"Summary parsing failed: {str(e)}"

    def _get_fallback_articles(self, count: int) -> List[Dict]:
        """Fallback article generator (unchanged)"""
        return [
            {
                "title": f"Fallback News {i}",
                "description": f"This is sample news article #{i}",
                "category": ["Technology", "Business", "Science"][i % 3],
                "source_name": "FallbackSource",
                "relevance_score": round(0.8 + (i * 0.05), 2),
                "latitude": 37.7897 + (i * 0.1),
                "longitude": -122.4194 + (i * 0.1)
            }
            for i in range(count)
        ]