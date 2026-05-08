import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from llm_orchestrator import generate_content

# Load environment variables
load_dotenv()


def analyze_page(url: str) -> str:
    """
    Fetch a webpage and extract useful element information for the AI.
    Returns a summary of interactive elements (inputs, buttons, links, etc.)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        elements = []
        
        # Find all input elements
        for inp in soup.find_all('input'):
            info = {
                'tag': 'input',
                'type': inp.get('type', 'text'),
                'id': inp.get('id'),
                'name': inp.get('name'),
                'placeholder': inp.get('placeholder'),
                'class': ' '.join(inp.get('class', []))
            }
            elements.append({k: v for k, v in info.items() if v})
        
        # Find all buttons
        for btn in soup.find_all(['button', 'input[type="submit"]']):
            info = {
                'tag': 'button',
                'id': btn.get('id'),
                'text': btn.get_text(strip=True)[:50],
                'type': btn.get('type'),
                'class': ' '.join(btn.get('class', []))
            }
            elements.append({k: v for k, v in info.items() if v})
        
        # Find text areas
        for ta in soup.find_all('textarea'):
            info = {
                'tag': 'textarea',
                'id': ta.get('id'),
                'name': ta.get('name'),
                'placeholder': ta.get('placeholder')
            }
            elements.append({k: v for k, v in info.items() if v})
        
        # Find forms
        forms = soup.find_all('form')
        form_info = [{'tag': 'form', 'id': f.get('id'), 'action': f.get('action')} for f in forms]
        
        # Find key divs/spans that might show messages
        for el in soup.find_all(['div', 'span', 'p']):
            if el.get('id') and any(word in (el.get('id') or '').lower() 
                                    for word in ['message', 'error', 'alert', 'status', 'result', 'notification']):
                elements.append({
                    'tag': el.name,
                    'id': el.get('id'),
                    'purpose': 'likely message/status display'
                })
        
        return json.dumps({
            'forms': form_info,
            'interactive_elements': elements[:30]  # Limit to avoid token overload
        }, indent=2)
        
    except Exception as e:
        return f"Could not analyze page: {str(e)}"


def generate_test_steps(requirement: str, url: str = None):
    """
    Converts a natural language requirement into structured test steps.
    If URL is provided, analyzes the page first for better accuracy.
    Output is STRICT JSON for Selenium compatibility.
    """
    
    # Analyze page if URL provided
    page_context = ""
    if url:
        page_analysis = analyze_page(url)
        page_context = f"""
Page Analysis (elements found on the target page):
{page_analysis}

Use the actual element IDs, names, or classes from this analysis when possible.
"""

    prompt = f"""
You are an expert QA automation engineer.

Requirement to test:
"{requirement}"

Target URL: {url or "Not specified"}
{page_context}

Task:
Generate test steps as STRICT JSON that can be executed by Selenium.

Available actions:
- "navigate" - Opens the URL (always first step)
- "input" - Types text into a field
- "click" - Clicks an element  
- "check" - Verifies text is present in an element
- "wait" - Waits for specified milliseconds

Selector types (use the most reliable available):
- "id" - Element ID (most reliable if available)
- "name" - Element name attribute
- "css" - CSS selector (e.g., ".classname", "button[type='submit']")
- "xpath" - XPath selector (use as last resort)
- "tag" - HTML tag name

Rules:
1. Output ONLY valid JSON array - no markdown, no explanations
2. Use actual selectors from the page analysis when available
3. Prefer ID selectors, then name, then CSS
4. For check actions, use SINGLE KEYWORDS that indicate success/failure, not full sentences:
   - Good examples: "error", "invalid", "failed", "success", "welcome", "password", "characters"
   - Bad examples: "Password must be at least 8 characters" (too specific, will fail)
5. Keep it simple - minimum steps needed to verify the requirement

JSON format:
[
  {{ "action": "navigate" }},
  {{ "action": "input", "selector": "username", "selectorType": "id", "value": "testuser" }},
  {{ "action": "click", "selector": "button[type='submit']", "selectorType": "css" }},
  {{ "action": "wait", "value": 1000 }},
  {{ "action": "check", "selector": "message", "selectorType": "id", "value": "expected text" }}
]
"""

    text = generate_content(prompt)
    
    # Clean up response - remove markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    
    try:
        steps = json.loads(text)
        # Add default selectorType if missing (backwards compatibility)
        for step in steps:
            if step.get("action") in ["input", "click", "check"] and "selectorType" not in step:
                step["selectorType"] = "id"
        return steps
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON returned by Gemini:\n{text}")


def explain_failure(requirement: str, steps, failure_reason: str):
    """
    Explains why a test failed and suggests a possible fix.
    Called ONLY when Selenium test fails.
    """

    prompt = f"""
You are a senior QA engineer analyzing a test failure.

Requirement being tested:
"{requirement}"

Test steps executed:
{json.dumps(steps, indent=2)}

Failure observed:
"{failure_reason}"

Provide:
1. A simple explanation of what went wrong
2. Possible causes (element not found, timing issue, wrong selector, etc.)
3. Suggested fix

Be concise and helpful. No markdown formatting.
"""

    return generate_content(prompt)