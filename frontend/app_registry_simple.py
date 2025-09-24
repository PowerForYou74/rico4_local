# frontend/app_registry_simple.py
from typing import Callable, Dict

class AppMeta:
    def __init__(self, key: str, name: str, icon: str, render: Callable, category: str = ""):
        self.key, self.name, self.icon, self.render, self.category = key, name, icon, render, category

REGISTRY: Dict[str, AppMeta] = {}

def register(app: AppMeta):
    REGISTRY[app.key] = app

def apps() -> Dict[str, AppMeta]:
    # Lade nur die System App
    if not REGISTRY:
        try:
            from .ui.apps.system import render
            register(AppMeta(
                key="system", name="System", icon="🛠️", render=render, category="Core"
            ))
        except ImportError as e:
            print(f"Warning: Could not load system app: {e}")
    return REGISTRY
