"""
Research service — live web search, source retrieval, evidence extraction.

Supports multiple search providers with graceful fallback.
"""
import re
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict
import httpx
from bs4 import BeautifulSoup

from backend.config import settings

logger = logging.getLogger(__name__)


def extract_json_from_llm(text: Optional[str]) -> Any:
    """
    Robustly extract and parse JSON from an LLM response.
    Handles:
    - Pure JSON
    - Markdown code blocks (```json ... ``` or ``` ...)
    - Conversational text preceding or following JSON
    - Outermost JSON array or object
    """
    if not text or not isinstance(text, str):
        return None
    cleaned = text.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Markdown block extraction (```json ... ``` or ``` ... ```)
    code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    for block in code_blocks:
        candidate = block.strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 3. Find outermost array [ ... ]
    first_bracket = cleaned.find('[')
    last_bracket = cleaned.rfind(']')
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')

    # If an array is the primary structure
    if first_bracket != -1 and last_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        candidate = cleaned[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # If an object is the primary structure
    if first_brace != -1 and last_brace != -1:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Try array as secondary if object failed
    if first_bracket != -1 and last_bracket != -1:
        candidate = cleaned[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None

# ── Search Provider Implementations ──────────────────────────────────────────

async def search_google_custom(query: str, num_results: int = 10) -> list[dict]:
    """Search using Google Custom Search JSON API."""
    if not settings.SEARCH_API_KEY or not settings.SEARCH_ENGINE_ID:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.SEARCH_API_KEY,
        "cx": settings.SEARCH_ENGINE_ID,
        "q": query,
        "num": min(num_results, 10),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for item in data.get("items", []):
        results.append({
            "url": item.get("link", ""),
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "publisher": item.get("displayLink", ""),
        })
    return results


async def search_serper(query: str, num_results: int = 10) -> list[dict]:
    """Search using Serper.dev API."""
    if not settings.SEARCH_API_KEY:
        return []
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": settings.SEARCH_API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=headers, json={"q": query, "num": num_results})
        resp.raise_for_status()
        data = resp.json()
    results = []
    for item in data.get("organic", []):
        results.append({
            "url": item.get("link", ""),
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "publisher": item.get("domain", ""),
        })
    return results


async def search_brave(query: str, num_results: int = 10) -> list[dict]:
    """Search using Brave Search API."""
    if not settings.SEARCH_API_KEY:
        return []
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": settings.SEARCH_API_KEY}
    params = {"q": query, "count": num_results}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "snippet": item.get("description", ""),
            "publisher": item.get("meta_url", {}).get("hostname", ""),
        })
    return results


# ── Provider Dispatch ────────────────────────────────────────────────────────

SEARCH_PROVIDERS = {
    "google_custom": search_google_custom,
    "serper": search_serper,
    "brave": search_brave,
}


async def perform_web_search(query: str, num_results: int = 10) -> tuple[list[dict], str, bool]:
    """
    Execute web search using configured provider.
    Returns: (results, provider_name, is_live)
    """
    provider = settings.SEARCH_PROVIDER
    search_fn = SEARCH_PROVIDERS.get(provider)

    if not search_fn or not settings.search_configured:
        logger.warning(f"Search provider '{provider}' not configured. Returning empty results.")
        return [], provider, False

    try:
        results = await search_fn(query, num_results)
        return results, provider, True
    except Exception as e:
        logger.error(f"Search failed with provider '{provider}': {e}")
        return [], provider, False


# ── Page Content Extraction ──────────────────────────────────────────────────

async def fetch_page_content(url: str, max_chars: int = 15000) -> dict:
    """Fetch and extract text content from a web page."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Problem2ProjectAI/1.0 Research Bot"
            })
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Truncate
        if len(text) > max_chars:
            text = text[:max_chars] + "... [truncated]"

        # Try to find publication date
        pub_date = None
        for meta in soup.find_all("meta"):
            prop = meta.get("property", "") or meta.get("name", "")
            if "date" in prop.lower() or "published" in prop.lower():
                pub_date = meta.get("content", "")
                break

        return {
            "text": text,
            "title": soup.title.string if soup.title else "",
            "publication_date": pub_date,
            "success": True,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return {"text": "", "title": "", "publication_date": None, "success": False, "error": str(e)}


# ── AI Analysis ──────────────────────────────────────────────────────────────

async def analyze_with_ai(prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.5) -> Optional[str]:
    """Send a prompt to the configured AI provider and get a response."""
    if not settings.ai_configured:
        logger.warning("AI provider not configured")
        return None

    sys_msg = system_prompt or "You are an elite software architect and opportunity discovery engine. Return accurate, high-quality, strictly formatted output without conversational filler."

async def _call_google_ai_studio(prompt: str, sys_msg: Optional[str] = None, temperature: float = 0.3) -> Optional[str]:
    """Call Google AI Studio (Gemini) API directly via REST or via SDK."""
    api_key = settings.effective_google_api_key
    if not api_key:
        return None
    model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"

    # 1. Direct HTTPS REST endpoint (zero extra SDK dependency, fast, robust)
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        parts = []
        if sys_msg:
            parts.append({"text": f"System Directive: {sys_msg}\n\n"})
        parts.append({"text": prompt})
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 8192},
        }
        async with httpx.AsyncClient(timeout=75.0) as client:
            res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if content_parts:
                        return content_parts[0].get("text", "")
            else:
                logger.warning(f"Google AI Studio REST call failed ({res.status_code}): {res.text[:200]}")
    except Exception as e:
        logger.warning(f"Google AI Studio REST call exception: {e}")

    # 2. Fallback to google.genai SDK if available
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=f"{sys_msg}\n\n{prompt}" if sys_msg else prompt,
        )
        return response.text
    except Exception:
        pass

    # 3. Fallback to google.generativeai SDK if available
    try:
        import google.generativeai as gai
        gai.configure(api_key=api_key)
        model = gai.GenerativeModel(model_name)
        response = model.generate_content(f"{sys_msg}\n\n{prompt}" if sys_msg else prompt)
        return response.text
    except Exception:
        pass

    return None


async def analyze_with_ai(prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Optional[str]:
    """Execute analysis via configured AI provider (OpenRouter, Google AI Studio, or Anthropic)."""
    if not settings.ai_configured:
        logger.warning("AI provider not configured")
        return None

    sys_msg = system_prompt or "You are an elite software architect and opportunity discovery engine. Return accurate, high-quality, strictly formatted output without conversational filler."

    try:
        # If explicitly Google AI Studio or only Google API key provided
        if settings.AI_PROVIDER == "google" or (settings.effective_google_api_key and not settings.OPENROUTER_API_KEY):
            res_text = await _call_google_ai_studio(prompt, sys_msg=sys_msg, temperature=temperature)
            if res_text:
                return res_text
            # If Google failed, try openrouter fallback if available
            if settings.OPENROUTER_API_KEY:
                logger.info("Google AI Studio did not return content, attempting OpenRouter fallback...")

        # If OpenRouter is configured or selected
        if settings.AI_PROVIDER == "openrouter" or settings.OPENROUTER_API_KEY:
            async with httpx.AsyncClient(timeout=75.0) as client:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://problempilot.ai",
                        "X-Title": "ProblemPilot AI",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.OPENROUTER_MODEL,
                        "messages": [
                            {"role": "system", "content": sys_msg},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                elif res.status_code in (401, 402):
                    logger.error(f"OpenRouter API error {res.status_code}. Attempting Google AI Studio fallback if available...")
                    if settings.effective_google_api_key:
                        google_res = await _call_google_ai_studio(prompt, sys_msg=sys_msg, temperature=temperature)
                        if google_res:
                            return google_res
                else:
                    logger.error(f"OpenRouter API returned status {res.status_code}: {res.text[:200]}")

            # Fallback to Google AI Studio if OpenRouter was tried but returned nothing
            if settings.effective_google_api_key:
                google_res = await _call_google_ai_studio(prompt, sys_msg=sys_msg, temperature=temperature)
                if google_res:
                    return google_res

        elif settings.AI_PROVIDER == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        # Final safety fallback to Google AI Studio if available
        if settings.effective_google_api_key:
            try:
                return await _call_google_ai_studio(prompt, sys_msg=sys_msg, temperature=temperature)
            except Exception:
                pass
        return None


# ── Problem Extraction Prompt ────────────────────────────────────────────────

def build_analysis_prompt(query: str, sources: list[dict]) -> str:
    """Build a structured prompt for AI to extract problems from research sources."""
    source_text = ""
    for i, src in enumerate(sources, 1):
        source_text += f"\n--- Source {i}: {src.get('title', 'Unknown')} ---\n"
        source_text += f"URL: {src.get('url', '')}\n"
        source_text += f"Content: {src.get('text', src.get('snippet', ''))[:3000]}\n"

    return f"""You are a research analyst identifying real-world problems worth solving with technology.

Research Query: {query}

Sources found:
{source_text}

Analyze these sources and identify 3-5 distinct real-world problems. For each problem, provide a JSON array with objects containing:

1. "title": A clear problem statement (string)
2. "description": Detailed explanation of the problem (string)
3. "affected_users": Who is affected and estimated scale (string)
4. "existing_solutions": Current solutions and their limitations (string)
5. "solution_gaps": What's missing from current solutions (string)
6. "evidence_summary": Key evidence from the sources (string)
7. "claim_type": One of "verified_fact", "source_backed", "inference", "hypothesis"
8. "scores": An object with these dimensions, each having "score" (0-10), "explanation", and "confidence" ("high"/"medium"/"low"):
   - "severity": How serious is the problem
   - "scale": How many people are affected
   - "evidence_strength": How well-supported by sources
   - "urgency": How time-sensitive
   - "feasibility": How feasible to build a solution
   - "differentiation": How much room for a better solution
   - "effort": Estimated development effort (10=easy, 0=very hard)
9. "evidence_gaps": Array of strings — what evidence is missing
10. "contradictions": Array of strings — any conflicting evidence found

IMPORTANT:
- Only cite information actually present in the sources
- Mark claims appropriately: don't label inferences as verified facts
- Identify evidence gaps honestly
- Do NOT invent statistics, market sizes, or quotes

Return ONLY a valid JSON array. No markdown, no explanation outside the JSON."""


def build_scoring_weights() -> dict:
    """Default scoring weights for opportunity evaluation."""
    return {
        "severity": 0.15,
        "scale": 0.12,
        "evidence_strength": 0.15,
        "urgency": 0.10,
        "feasibility": 0.15,
        "differentiation": 0.13,
        "effort": 0.10,
        "data_availability": 0.10,
    }
