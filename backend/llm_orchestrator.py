import os
import google.generativeai as genai

import requests

try:
    from groq import Groq
except ImportError:
    Groq = None

def get_gemini_keys():
    """Discover all provided Gemini API keys from environment variables."""
    keys = []
    primary_key = os.getenv("GEMINI_API_KEY")
    if primary_key:
        keys.append(primary_key)
        
    for i in range(1, 10):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key and key not in keys:
            keys.append(key)
            
    return keys


def _call_gemini(prompt: str, api_key: str) -> str:
    """Wrapper for Google Gemini."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # Normalize model name for older google-generativeai versions if needed, but 'gemini-2.5-flash' works
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text.strip()


def _call_mistral(prompt: str, api_key: str) -> str:
    """Wrapper for Mistral AI using raw requests to avoid SDK dependency issues."""
    model_name = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _call_groq(prompt: str, api_key: str) -> str:
    """Wrapper for Groq."""
    if not Groq:
        raise ImportError("groq package not installed")
        
    client = Groq(api_key=api_key)
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_content(prompt: str) -> str:
    """
    Unified LLM invocation interface.
    Implements cascading fallback: Gemini (with key rotation) -> Mistral -> Groq.
    """
    last_error = None
    
    # 1. Attempt Gemini (with rotation)
    gemini_keys = get_gemini_keys()
    for i, key in enumerate(gemini_keys):
        try:
            print(f"[Orchestrator] Attempting Gemini API (Key #{i+1})...")
            return _call_gemini(prompt, key)
        except Exception as e:
            last_error = e
            print(f"[Orchestrator] Gemini Key #{i+1} failed: {type(e).__name__}. Rotating...")
            continue
            
    # 2. Attempt Mistral Fallback
    mistral_key = os.getenv("MISTRAL_API_KEY")
    if mistral_key:
        try:
            print("[Orchestrator] Attempting Mistral AI fallback...")
            return _call_mistral(prompt, mistral_key)
        except Exception as e:
            last_error = e
            print(f"[Orchestrator] Mistral fallback failed: {type(e).__name__}.")
    else:
        print("[Orchestrator] Mistral API key missing. Skipping Mistral fallback...")
        
    # 3. Attempt Groq Fallback
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            print("[Orchestrator] Attempting Groq fallback...")
            return _call_groq(prompt, groq_key)
        except Exception as e:
            last_error = e
            print(f"[Orchestrator] Groq fallback failed: {type(e).__name__}.")
    else:
        print("[Orchestrator] Groq API key missing. Skipping Groq fallback...")
        
    # 4. Total Exhaustion
    raise RuntimeError(f"All available LLM providers failed. Last error: {last_error}")
