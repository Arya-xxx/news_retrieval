import os
import re
import requests
import json
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY in environment variables")

        self.model = "gemini-1.5-flash"  # Fast model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.timeout = 30

    def _make_api_request(self, payload: Dict) -> Tuple[Optional[Dict], Optional[str]]:
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

    def _safe_json_parse(self, text: str):
        """
        Try to parse JSON directly. If that fails, extract the first JSON array found in the text.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Extract JSON array from any surrounding text, handling newlines and spacing
            match = re.search(r"\[\s*\{.*?\}\s*\]", text, re.S)
            if match:
                return json.loads(match.group(0))
            raise ValueError("No valid JSON array found in response")

    def generate_news_articles(
        self,
        category: str,
        count: int = 5,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: int = 500,
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Generate news articles filtered by category and optionally by location.

        Args:
            category: News category (Technology, Business, Science).
            count: Number of articles to generate.
            latitude: Optional latitude to focus news generation near.
            longitude: Optional longitude to focus news generation near.
            radius_km: Radius in kilometers around location.

        Returns:
            Tuple of list of articles and optional error string.
        """
        location_context = ""
        if latitude is not None and longitude is not None:
            location_context = (
                f" around latitude {latitude}, longitude {longitude} "
                f"within approximately {radius_km} kilometers radius"
            )

        prompt = f"""Generate exactly {count} diverse news articles of category '{category}'{location_context}.
Output strictly in JSON array format (no extra text).

Each article must have:
- title (string)
- description (string)
- category (Technology, Business, or Science)
- source_name (string)
- relevance_score (0-1)
- latitude (float)
- longitude (float)

Example output:
[
    {{
        "title": "Sample",
        "description": "Sample description",
        "category": "Technology",
        "source_name": "NewsSource",
        "relevance_score": 0.9,
        "latitude": 37.7749,
        "longitude": -122.4194
    }}
]"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json"  # Use camelCase
            }
        }

        result, error = self._make_api_request(payload)
        if error:
            return self._get_fallback_articles(count), error

        try:
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            articles = self._safe_json_parse(response_text)
            if not isinstance(articles, list):
                raise ValueError("API did not return a list of articles")
            return articles, None
        except Exception as e:
            return self._get_fallback_articles(count), f"Response parsing failed: {str(e)}"

    def generate_summary(self, text: str, max_length: int = 200) -> Tuple[str, Optional[str]]:
        """
        Generate a concise summary of the given text.

        Args:
            text: Text to summarize.
            max_length: Maximum length of summary in characters.

        Returns:
            Tuple of summary string and optional error message.
        """
        prompt = f"""Summarize the following text in 1-2 sentences, under {max_length} characters.
Return only the summary text, no extra formatting.

{text}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 100,
                "temperature": 0.3
            }
        }

        result, error = self._make_api_request(payload)
        if error:
            return self._truncate_fallback(text, max_length), error

        try:
            summary = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if len(summary) > max_length:
                summary = summary[:max_length - 3] + "..."
            return summary, None
        except Exception as e:
            return self._truncate_fallback(text, max_length), f"Summary parsing failed: {str(e)}"

    def _truncate_fallback(self, text: str, max_length: int) -> str:
        """
        Simple fallback summary by truncating text.
        """
        return text[:max_length].rsplit(" ", 1)[0] + "..." if len(text) > max_length else text

    def _get_fallback_articles(self, count: int) -> List[Dict]:
        """
        Provide fallback sample articles if API call fails.
        """
        return [
            {
                "title": f"Fallback News {i+1}",
                "description": f"This is sample news article #{i+1}",
                "category": ["Technology", "Business", "Science"][i % 3],
                "source_name": "FallbackSource",
                "relevance_score": round(0.8 + (i * 0.05), 2),
                "latitude": 37.7897 + (i * 0.1),
                "longitude": -122.4194 + (i * 0.1),
            }
            for i in range(count)
        ]


__all__ = ["GeminiService"]
