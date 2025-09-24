# frontend/app_registry.py
from typing import Callable, Dict, List, Tuple
import importlib

class AppMeta:
    def __init__(self, key: str, name: str, icon: str, render: Callable, category: str = ""):
        self.key, self.name, self.icon, self.render, self.category = key, name, icon, render, category

REGISTRY: Dict[str, AppMeta] = {}
LOAD_ERRORS: List[Tuple[str, str]] = []

def register(app: AppMeta):
    REGISTRY[app.key] = app

def apps() -> Dict[str, AppMeta]:
    return REGISTRY

# 🔸 Neu: deterministische Liste der App-Module
APPS_TO_LOAD = [
    "ui.apps.tierheilpraxis",
    "ui.apps.cashbot", 
    "ui.apps.research",
    "ui.apps.automations",
    "ui.apps.system",
]

def autoload() -> Dict[str, AppMeta]:
    """Importiert die App-Module und füllt REGISTRY via register(...)."""
    if REGISTRY:  # schon geladen
        return REGISTRY
    for mod in APPS_TO_LOAD:
        try:
            importlib.import_module(mod)
        except Exception as e:
            LOAD_ERRORS.append((mod, str(e)))
    return REGISTRY
