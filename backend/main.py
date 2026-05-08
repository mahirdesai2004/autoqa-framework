from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import List, Dict, Any, Optional

# Import business logic
from backend.ai_agent import generate_test_steps, explain_failure
from backend.evaluation_layer import evaluate, validate_steps
from backend.selenium_runner import run_test
from backend.notifications import send_slack_notification

app = FastAPI(title="AutoQA API", version="0.2.0")

class GenerateRequest(BaseModel):
    requirement: str
    url: str

class TestExecutionRequest(BaseModel):
    steps: List[Dict[str, Any]]
    url: str

@app.get("/api/v1/status")
async def status():
    """Returns the orchestration status and configured providers."""
    providers = []
    if os.getenv("GEMINI_API_KEY"): providers.append("Gemini")
    if os.getenv("MISTRAL_API_KEY"): providers.append("Mistral")
    if os.getenv("GROQ_API_KEY"): providers.append("Groq")
    
    return {
        "status": "online",
        "providers_configured": providers
    }

@app.post("/api/v1/generate-steps")
async def api_generate_steps(req: GenerateRequest):
    """Generates execution steps using the LLM orchestrator."""
    try:
        steps = generate_test_steps(req.requirement, req.url)
        is_valid, msg = validate_steps(steps)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Validation failed: {msg}")
        return {"steps": steps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/run-test")
async def api_run_test(req: TestExecutionRequest):
    """Executes the generated steps via Selenium."""
    try:
        result, reason, screenshot_path = run_test(req.steps, req.url)
        
        # Trigger Notification
        if result == "PASS":
            send_slack_notification(f"✅ AutoQA Execution Passed", f"Target: {req.url}\nSteps Executed: {len(req.steps)}", status="success")
        else:
            send_slack_notification(f"❌ AutoQA Execution Failed", f"Target: {req.url}\nReason: {reason}", status="error")
            
        return {
            "result": result,
            "reason": reason,
            "screenshot": screenshot_path
        }
    except Exception as e:
        send_slack_notification(f"⚠️ AutoQA Pipeline Error", str(e), status="error")
        raise HTTPException(status_code=500, detail=str(e))
