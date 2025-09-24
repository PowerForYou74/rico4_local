import os
import requests

BASE = os.getenv("UI_API_BASE", "http://localhost:8000")

def get(p, **kw):
    return requests.get(f"{BASE}{p}", timeout=kw.get("timeout", 15), params=kw.get("params")).json()

def post(p, payload=None, **kw):
    return requests.post(f"{BASE}{p}", json=payload, timeout=kw.get("timeout", 30)).json()

def post_form(p, files):
    return requests.post(f"{BASE}{p}", files=files, timeout=60).json()
