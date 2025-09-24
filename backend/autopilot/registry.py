# backend/autopilot/registry.py
"""
Autopilot Registry - Prompt/Policy Registry mit Versioning
Verwaltet Prompts, Policies und deren Versionen
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

# ------------------------------------------------------------
# Enums
# ------------------------------------------------------------

class PromptStatus(Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class PolicyType(Enum):
    ROUTING = "routing"
    QUALITY = "quality"
    SAFETY = "safety"
    COST = "cost"

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

@dataclass
class PromptVersion:
    """Version eines Prompts"""
    id: str
    prompt_id: str
    version: str
    content: str
    role: str
    tags: List[str]
    created_at: datetime
    created_by: str = "autopilot"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Prompt:
    """Prompt mit Versionen"""
    id: str
    name: str
    description: str
    current_version: str
    status: PromptStatus
    created_at: datetime
    updated_at: datetime
    versions: Dict[str, PromptVersion] = None
    
    def __post_init__(self):
        if self.versions is None:
            self.versions = {}

@dataclass
class PolicyVersion:
    """Version einer Policy"""
    id: str
    policy_id: str
    version: str
    policy_type: PolicyType
    config: Dict[str, Any]
    created_at: datetime
    created_by: str = "autopilot"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Policy:
    """Policy mit Versionen"""
    id: str
    name: str
    description: str
    policy_type: PolicyType
    current_version: str
    status: PromptStatus
    created_at: datetime
    updated_at: datetime
    versions: Dict[str, PolicyVersion] = None
    
    def __post_init__(self):
        if self.versions is None:
            self.versions = {}

@dataclass
class ChangelogEntry:
    """Changelog-Eintrag"""
    id: str
    timestamp: datetime
    action: str  # "created", "updated", "promoted", "deprecated", "rolled_back"
    entity_type: str  # "prompt", "policy"
    entity_id: str
    version: str
    description: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

# ------------------------------------------------------------
# Registry Manager
# ------------------------------------------------------------

class RegistryManager:
    """Verwaltet das Prompt/Policy Registry"""
    
    def __init__(self, registry_path: str = "data/autopilot/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        self.prompts_file = self.registry_path / "prompts.json"
        self.policies_file = self.registry_path / "policies.json"
        self.changelog_file = self.registry_path / "changelog.json"
        
        # Lade bestehende Daten
        self.prompts = self._load_prompts()
        self.policies = self._load_policies()
        self.changelog = self._load_changelog()
    
    def _load_prompts(self) -> Dict[str, Prompt]:
        """Lädt Prompts aus Datei"""
        if not self.prompts_file.exists():
            return {}
        
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                prompts = {}
                
                for prompt_id, prompt_data in data.items():
                    # Konvertiere Status
                    status = PromptStatus(prompt_data.get('status', 'draft'))
                    
                    # Konvertiere Versionen
                    versions = {}
                    for version_id, version_data in prompt_data.get('versions', {}).items():
                        version = PromptVersion(**version_data)
                        versions[version_id] = version
                    
                    prompt = Prompt(
                        id=prompt_data['id'],
                        name=prompt_data['name'],
                        description=prompt_data['description'],
                        current_version=prompt_data['current_version'],
                        status=status,
                        created_at=datetime.fromisoformat(prompt_data['created_at']),
                        updated_at=datetime.fromisoformat(prompt_data['updated_at']),
                        versions=versions
                    )
                    prompts[prompt_id] = prompt
                
                return prompts
        except Exception as e:
            print(f"Error loading prompts: {e}")
            return {}
    
    def _load_policies(self) -> Dict[str, Policy]:
        """Lädt Policies aus Datei"""
        if not self.policies_file.exists():
            return {}
        
        try:
            with open(self.policies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                policies = {}
                
                for policy_id, policy_data in data.items():
                    # Konvertiere Enums
                    policy_type = PolicyType(policy_data.get('policy_type', 'routing'))
                    status = PromptStatus(policy_data.get('status', 'draft'))
                    
                    # Konvertiere Versionen
                    versions = {}
                    for version_id, version_data in policy_data.get('versions', {}).items():
                        version = PolicyVersion(**version_data)
                        versions[version_id] = version
                    
                    policy = Policy(
                        id=policy_data['id'],
                        name=policy_data['name'],
                        description=policy_data['description'],
                        policy_type=policy_type,
                        current_version=policy_data['current_version'],
                        status=status,
                        created_at=datetime.fromisoformat(policy_data['created_at']),
                        updated_at=datetime.fromisoformat(policy_data['updated_at']),
                        versions=versions
                    )
                    policies[policy_id] = policy
                
                return policies
        except Exception as e:
            print(f"Error loading policies: {e}")
            return {}
    
    def _load_changelog(self) -> List[ChangelogEntry]:
        """Lädt Changelog aus Datei"""
        if not self.changelog_file.exists():
            return []
        
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ChangelogEntry(**entry) for entry in data]
        except Exception as e:
            print(f"Error loading changelog: {e}")
            return []
    
    def _save_prompts(self):
        """Speichert Prompts"""
        data = {}
        for prompt_id, prompt in self.prompts.items():
            data[prompt_id] = {
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "current_version": prompt.current_version,
                "status": prompt.status.value,
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat(),
                "versions": {
                    version_id: asdict(version) for version_id, version in prompt.versions.items()
                }
            }
        
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_policies(self):
        """Speichert Policies"""
        data = {}
        for policy_id, policy in self.policies.items():
            data[policy_id] = {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "policy_type": policy.policy_type.value,
                "current_version": policy.current_version,
                "status": policy.status.value,
                "created_at": policy.created_at.isoformat(),
                "updated_at": policy.updated_at.isoformat(),
                "versions": {
                    version_id: asdict(version) for version_id, version in policy.versions.items()
                }
            }
        
        with open(self.policies_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_changelog(self):
        """Speichert Changelog"""
        data = [asdict(entry) for entry in self.changelog]
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _add_changelog_entry(self, 
                           action: str,
                           entity_type: str,
                           entity_id: str,
                           version: str,
                           description: str,
                           metadata: Dict[str, Any] = None):
        """Fügt Changelog-Eintrag hinzu"""
        
        entry = ChangelogEntry(
            id=f"changelog_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            description=description,
            metadata=metadata or {}
        )
        
        self.changelog.append(entry)
        self._save_changelog()

# ------------------------------------------------------------
# Prompt Registry
# ------------------------------------------------------------

class PromptRegistry:
    """Verwaltet Prompt-Registry"""
    
    def __init__(self, registry_manager: RegistryManager):
        self.registry = registry_manager
    
    def register_prompt(self, 
                       name: str,
                       content: str,
                       role: str = "system",
                       description: str = "",
                       tags: List[str] = None) -> str:
        """Registriert neuen Prompt"""
        
        if tags is None:
            tags = []
        
        prompt_id = f"prompt_{uuid.uuid4().hex[:8]}"
        version_id = f"v1_{uuid.uuid4().hex[:8]}"
        
        # Erstelle Prompt
        prompt = Prompt(
            id=prompt_id,
            name=name,
            description=description,
            current_version=version_id,
            status=PromptStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Erstelle erste Version
        version = PromptVersion(
            id=version_id,
            prompt_id=prompt_id,
            version="1.0.0",
            content=content,
            role=role,
            tags=tags,
            created_at=datetime.utcnow()
        )
        
        prompt.versions[version_id] = version
        self.registry.prompts[prompt_id] = prompt
        self.registry._save_prompts()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="created",
            entity_type="prompt",
            entity_id=prompt_id,
            version="1.0.0",
            description=f"Created prompt '{name}'"
        )
        
        return prompt_id
    
    def add_version(self, 
                   prompt_id: str,
                   content: str,
                   version: str = None,
                   tags: List[str] = None) -> str:
        """Fügt neue Version zu Prompt hinzu"""
        
        if prompt_id not in self.registry.prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        prompt = self.registry.prompts[prompt_id]
        
        if version is None:
            # Auto-increment version
            current_version = prompt.current_version
            if current_version in prompt.versions:
                current_v = prompt.versions[current_version].version
                major, minor, patch = map(int, current_v.split('.'))
                version = f"{major}.{minor}.{patch + 1}"
            else:
                version = "1.0.0"
        
        version_id = f"v{version.replace('.', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Erstelle neue Version
        new_version = PromptVersion(
            id=version_id,
            prompt_id=prompt_id,
            version=version,
            content=content,
            role=prompt.versions[prompt.current_version].role,
            tags=tags or [],
            created_at=datetime.utcnow()
        )
        
        prompt.versions[version_id] = new_version
        prompt.updated_at = datetime.utcnow()
        self.registry._save_prompts()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="updated",
            entity_type="prompt",
            entity_id=prompt_id,
            version=version,
            description=f"Added version {version} to prompt '{prompt.name}'"
        )
        
        return version_id
    
    def promote_candidate(self, prompt_id: str, version_id: str) -> bool:
        """Befördert Kandidaten zu aktiv"""
        
        if prompt_id not in self.registry.prompts:
            return False
        
        prompt = self.registry.prompts[prompt_id]
        
        if version_id not in prompt.versions:
            return False
        
        # Aktualisiere Status
        prompt.status = PromptStatus.ACTIVE
        prompt.current_version = version_id
        prompt.updated_at = datetime.utcnow()
        
        # Deprecate andere Versionen
        for vid, version in prompt.versions.items():
            if vid != version_id:
                version.metadata["deprecated"] = True
        
        self.registry._save_prompts()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="promoted",
            entity_type="prompt",
            entity_id=prompt_id,
            version=prompt.versions[version_id].version,
            description=f"Promoted version {prompt.versions[version_id].version} of prompt '{prompt.name}' to active"
        )
        
        return True
    
    def rollback_prompt(self, prompt_id: str, target_version: str) -> bool:
        """Rollback zu vorheriger Version"""
        
        if prompt_id not in self.registry.prompts:
            return False
        
        prompt = self.registry.prompts[prompt_id]
        
        # Finde Ziel-Version
        target_version_id = None
        for vid, version in prompt.versions.items():
            if version.version == target_version:
                target_version_id = vid
                break
        
        if not target_version_id:
            return False
        
        # Rollback
        old_version = prompt.current_version
        prompt.current_version = target_version_id
        prompt.updated_at = datetime.utcnow()
        
        self.registry._save_prompts()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="rolled_back",
            entity_type="prompt",
            entity_id=prompt_id,
            version=target_version,
            description=f"Rolled back prompt '{prompt.name}' from {old_version} to {target_version}"
        )
        
        return True
    
    def get_active_prompt(self, prompt_id: str) -> Optional[PromptVersion]:
        """Gibt aktive Version eines Prompts zurück"""
        
        if prompt_id not in self.registry.prompts:
            return None
        
        prompt = self.registry.prompts[prompt_id]
        
        if prompt.status != PromptStatus.ACTIVE:
            return None
        
        return prompt.versions.get(prompt.current_version)
    
    def list_prompts(self, status: Optional[PromptStatus] = None) -> List[Prompt]:
        """Listet Prompts auf"""
        
        prompts = list(self.registry.prompts.values())
        
        if status:
            prompts = [p for p in prompts if p.status == status]
        
        return sorted(prompts, key=lambda p: p.updated_at, reverse=True)

# ------------------------------------------------------------
# Policy Registry
# ------------------------------------------------------------

class PolicyRegistry:
    """Verwaltet Policy-Registry"""
    
    def __init__(self, registry_manager: RegistryManager):
        self.registry = registry_manager
    
    def register_policy(self, 
                       name: str,
                       policy_type: PolicyType,
                       config: Dict[str, Any],
                       description: str = "") -> str:
        """Registriert neue Policy"""
        
        policy_id = f"policy_{uuid.uuid4().hex[:8]}"
        version_id = f"v1_{uuid.uuid4().hex[:8]}"
        
        # Erstelle Policy
        policy = Policy(
            id=policy_id,
            name=name,
            description=description,
            policy_type=policy_type,
            current_version=version_id,
            status=PromptStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Erstelle erste Version
        version = PolicyVersion(
            id=version_id,
            policy_id=policy_id,
            version="1.0.0",
            policy_type=policy_type,
            config=config,
            created_at=datetime.utcnow()
        )
        
        policy.versions[version_id] = version
        self.registry.policies[policy_id] = policy
        self.registry._save_policies()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="created",
            entity_type="policy",
            entity_id=policy_id,
            version="1.0.0",
            description=f"Created {policy_type.value} policy '{name}'"
        )
        
        return policy_id
    
    def update_policy(self, 
                     policy_id: str,
                     config: Dict[str, Any],
                     version: str = None) -> str:
        """Aktualisiert Policy"""
        
        if policy_id not in self.registry.policies:
            raise ValueError(f"Policy {policy_id} not found")
        
        policy = self.registry.policies[policy_id]
        
        if version is None:
            # Auto-increment version
            current_version = policy.current_version
            if current_version in policy.versions:
                current_v = policy.versions[current_version].version
                major, minor, patch = map(int, current_v.split('.'))
                version = f"{major}.{minor}.{patch + 1}"
            else:
                version = "1.0.0"
        
        version_id = f"v{version.replace('.', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Erstelle neue Version
        new_version = PolicyVersion(
            id=version_id,
            policy_id=policy_id,
            version=version,
            policy_type=policy.policy_type,
            config=config,
            created_at=datetime.utcnow()
        )
        
        policy.versions[version_id] = new_version
        policy.updated_at = datetime.utcnow()
        self.registry._save_policies()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="updated",
            entity_type="policy",
            entity_id=policy_id,
            version=version,
            description=f"Updated {policy.policy_type.value} policy '{policy.name}' to version {version}"
        )
        
        return version_id
    
    def promote_policy(self, policy_id: str, version_id: str) -> bool:
        """Befördert Policy zu aktiv"""
        
        if policy_id not in self.registry.policies:
            return False
        
        policy = self.registry.policies[policy_id]
        
        if version_id not in policy.versions:
            return False
        
        # Aktualisiere Status
        policy.status = PromptStatus.ACTIVE
        policy.current_version = version_id
        policy.updated_at = datetime.utcnow()
        
        self.registry._save_policies()
        
        # Changelog
        self.registry._add_changelog_entry(
            action="promoted",
            entity_type="policy",
            entity_id=policy_id,
            version=policy.versions[version_id].version,
            description=f"Promoted {policy.policy_type.value} policy '{policy.name}' to active"
        )
        
        return True
    
    def get_active_policy(self, policy_id: str) -> Optional[PolicyVersion]:
        """Gibt aktive Version einer Policy zurück"""
        
        if policy_id not in self.registry.policies:
            return None
        
        policy = self.registry.policies[policy_id]
        
        if policy.status != PromptStatus.ACTIVE:
            return None
        
        return policy.versions.get(policy.current_version)
    
    def list_policies(self, 
                     policy_type: Optional[PolicyType] = None,
                     status: Optional[PromptStatus] = None) -> List[Policy]:
        """Listet Policies auf"""
        
        policies = list(self.registry.policies.values())
        
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        
        if status:
            policies = [p for p in policies if p.status == status]
        
        return sorted(policies, key=lambda p: p.updated_at, reverse=True)

# ------------------------------------------------------------
# Globale Instanzen
# ------------------------------------------------------------

_registry_manager: Optional[RegistryManager] = None
_prompt_registry: Optional[PromptRegistry] = None
_policy_registry: Optional[PolicyRegistry] = None

def get_registry_manager() -> RegistryManager:
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = RegistryManager()
    return _registry_manager

def get_prompt_registry() -> PromptRegistry:
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = PromptRegistry(get_registry_manager())
    return _prompt_registry

def get_policy_registry() -> PolicyRegistry:
    global _policy_registry
    if _policy_registry is None:
        _policy_registry = PolicyRegistry(get_registry_manager())
    return _policy_registry
