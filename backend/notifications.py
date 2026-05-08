import os
import requests
import json
from datetime import datetime

def send_slack_notification(message: str, details: str = None, status: str = "info"):
    """
    Sends an optional notification to a Slack webhook if SLACK_WEBHOOK_URL is configured.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return # Gracefully do nothing if not configured
        
    color_map = {
        "success": "#10b981", # Emerald
        "error": "#ef4444",   # Red
        "warning": "#f59e0b", # Amber
        "info": "#3b82f6"     # Blue
    }
    
    payload = {
        "text": message,
        "attachments": [
            {
                "color": color_map.get(status, "#cbd5e1"),
                "fields": [
                    {
                        "title": "Status",
                        "value": status.upper(),
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": datetime.utcnow().isoformat() + "Z",
                        "short": True
                    }
                ]
            }
        ]
    }
    
    if details:
        payload["attachments"][0]["fields"].append({
            "title": "Details",
            "value": details,
            "short": False
        })
        
    try:
        # Fire-and-forget notification
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"[Notifications] Failed to send webhook: {e}")
