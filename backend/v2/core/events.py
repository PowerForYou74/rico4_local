import os
import requests

def queue_event(event: dict):
    url = os.getenv("N8N_EVENT_WEBHOOK")
    if not url:
        return {"queued": False, "reason": "no webhook"}
    try:
        r = requests.post(url, json=event, timeout=10)
        return {"queued": True, "status": r.status_code}
    except Exception:
        return {"queued": False, "reason": "send_error"}
