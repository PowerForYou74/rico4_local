# backend/tests/autopilot/test_registry.py
"""
Tests für Autopilot Registry
"""

import pytest
import tempfile
import os
from datetime import datetime
from backend.autopilot.registry import (
    RegistryManager, PromptRegistry, PolicyRegistry,
    PromptVersion, Prompt, PolicyVersion, Policy,
    PromptStatus, PolicyType, ChangelogEntry
)

class TestRegistryManager:
    """Tests für RegistryManager"""
    
    @pytest.fixture
    def temp_registry(self):
        """Erstellt temporäres Registry-Verzeichnis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def manager(self, temp_registry):
        return RegistryManager(temp_registry)
    
    def test_registry_manager_init(self, manager):
        """Test RegistryManager Initialisierung"""
        assert manager.registry_path.exists()
        assert manager.prompts_file.exists() or not manager.prompts_file.exists()
        assert manager.policies_file.exists() or not manager.policies_file.exists()
        assert manager.changelog_file.exists() or not manager.changelog_file.exists()
    
    def test_add_changelog_entry(self, manager):
        """Test Changelog-Eintrag hinzufügen"""
        manager._add_changelog_entry(
            action="test_action",
            entity_type="test_entity",
            entity_id="test_id",
            version="1.0.0",
            description="Test description"
        )
        
        assert len(manager.changelog) == 1
        entry = manager.changelog[0]
        assert entry.action == "test_action"
        assert entry.entity_type == "test_entity"
        assert entry.entity_id == "test_id"
        assert entry.version == "1.0.0"
        assert entry.description == "Test description"

class TestPromptRegistry:
    """Tests für PromptRegistry"""
    
    @pytest.fixture
    def temp_registry(self):
        """Erstellt temporäres Registry-Verzeichnis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def registry(self, temp_registry):
        manager = RegistryManager(temp_registry)
        return PromptRegistry(manager)
    
    def test_register_prompt(self, registry):
        """Test Prompt registrieren"""
        prompt_id = registry.register_prompt(
            name="Test Prompt",
            content="Du bist ein hilfreicher Assistent.",
            role="system",
            description="Test prompt for testing",
            tags=["test", "assistant"]
        )
        
        assert prompt_id is not None
        assert prompt_id in registry.registry.prompts
        
        prompt = registry.registry.prompts[prompt_id]
        assert prompt.name == "Test Prompt"
        assert prompt.description == "Test prompt for testing"
        assert prompt.status == PromptStatus.DRAFT
        assert len(prompt.versions) == 1
    
    def test_add_version(self, registry):
        """Test Version zu Prompt hinzufügen"""
        # Erstelle Prompt
        prompt_id = registry.register_prompt(
            name="Test Prompt",
            content="Original content",
            role="system"
        )
        
        # Füge neue Version hinzu
        version_id = registry.add_version(
            prompt_id=prompt_id,
            content="Updated content",
            version="2.0.0",
            tags=["updated"]
        )
        
        assert version_id is not None
        prompt = registry.registry.prompts[prompt_id]
        assert len(prompt.versions) == 2
        assert version_id in prompt.versions
    
    def test_promote_candidate(self, registry):
        """Test Kandidaten befördern"""
        # Erstelle Prompt
        prompt_id = registry.register_prompt(
            name="Test Prompt",
            content="Original content",
            role="system"
        )
        
        # Füge Version hinzu
        version_id = registry.add_version(
            prompt_id=prompt_id,
            content="Updated content"
        )
        
        # Befördere Kandidaten
        success = registry.promote_candidate(prompt_id, version_id)
        assert success is True
        
        prompt = registry.registry.prompts[prompt_id]
        assert prompt.status == PromptStatus.ACTIVE
        assert prompt.current_version == version_id
    
    def test_rollback_prompt(self, registry):
        """Test Prompt-Rollback"""
        # Erstelle Prompt mit mehreren Versionen
        prompt_id = registry.register_prompt(
            name="Test Prompt",
            content="Version 1",
            role="system"
        )
        
        version_1 = list(registry.registry.prompts[prompt_id].versions.keys())[0]
        
        # Füge zweite Version hinzu
        version_id_2 = registry.add_version(
            prompt_id=prompt_id,
            content="Version 2"
        )
        
        # Befördere zweite Version
        registry.promote_candidate(prompt_id, version_id_2)
        
        # Rollback zur ersten Version
        success = registry.rollback_prompt(prompt_id, "1.0.0")
        assert success is True
        
        prompt = registry.registry.prompts[prompt_id]
        assert prompt.current_version == version_1
    
    def test_get_active_prompt(self, registry):
        """Test aktiven Prompt abrufen"""
        # Erstelle und befördere Prompt
        prompt_id = registry.register_prompt(
            name="Test Prompt",
            content="Active content",
            role="system"
        )
        
        version_id = list(registry.registry.prompts[prompt_id].versions.keys())[0]
        registry.promote_candidate(prompt_id, version_id)
        
        # Hole aktiven Prompt
        active_prompt = registry.get_active_prompt(prompt_id)
        assert active_prompt is not None
        assert active_prompt.content == "Active content"
    
    def test_get_active_prompt_nonexistent(self, registry):
        """Test aktiven Prompt für nicht existierenden Prompt"""
        active_prompt = registry.get_active_prompt("nonexistent_id")
        assert active_prompt is None
    
    def test_list_prompts(self, registry):
        """Test Prompt-Liste"""
        # Erstelle mehrere Prompts
        for i in range(3):
            registry.register_prompt(
                name=f"Test Prompt {i}",
                content=f"Content {i}",
                role="system"
            )
        
        # Liste alle Prompts
        prompts = registry.list_prompts()
        assert len(prompts) == 3
        
        # Liste nur aktive Prompts
        active_prompts = registry.list_prompts(status=PromptStatus.ACTIVE)
        assert len(active_prompts) == 0  # Keine befördert

class TestPolicyRegistry:
    """Tests für PolicyRegistry"""
    
    @pytest.fixture
    def temp_registry(self):
        """Erstellt temporäres Registry-Verzeichnis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def registry(self, temp_registry):
        manager = RegistryManager(temp_registry)
        return PolicyRegistry(manager)
    
    def test_register_policy(self, registry):
        """Test Policy registrieren"""
        policy_id = registry.register_policy(
            name="Test Policy",
            policy_type=PolicyType.ROUTING,
            config={"weights": {"openai": 0.6, "claude": 0.4}},
            description="Test routing policy"
        )
        
        assert policy_id is not None
        assert policy_id in registry.registry.policies
        
        policy = registry.registry.policies[policy_id]
        assert policy.name == "Test Policy"
        assert policy.policy_type == PolicyType.ROUTING
        assert policy.status == PromptStatus.DRAFT
        assert len(policy.versions) == 1
    
    def test_update_policy(self, registry):
        """Test Policy aktualisieren"""
        # Erstelle Policy
        policy_id = registry.register_policy(
            name="Test Policy",
            policy_type=PolicyType.ROUTING,
            config={"weights": {"openai": 0.6, "claude": 0.4}}
        )
        
        # Aktualisiere Policy
        version_id = registry.update_policy(
            policy_id=policy_id,
            config={"weights": {"openai": 0.7, "claude": 0.3}},
            version="2.0.0"
        )
        
        assert version_id is not None
        policy = registry.registry.policies[policy_id]
        assert len(policy.versions) == 2
    
    def test_promote_policy(self, registry):
        """Test Policy befördern"""
        # Erstelle Policy
        policy_id = registry.register_policy(
            name="Test Policy",
            policy_type=PolicyType.ROUTING,
            config={"weights": {"openai": 0.6, "claude": 0.4}}
        )
        
        version_id = list(registry.registry.policies[policy_id].versions.keys())[0]
        
        # Befördere Policy
        success = registry.promote_policy(policy_id, version_id)
        assert success is True
        
        policy = registry.registry.policies[policy_id]
        assert policy.status == PromptStatus.ACTIVE
        assert policy.current_version == version_id
    
    def test_get_active_policy(self, registry):
        """Test aktive Policy abrufen"""
        # Erstelle und befördere Policy
        policy_id = registry.register_policy(
            name="Test Policy",
            policy_type=PolicyType.ROUTING,
            config={"weights": {"openai": 0.6, "claude": 0.4}}
        )
        
        version_id = list(registry.registry.policies[policy_id].versions.keys())[0]
        registry.promote_policy(policy_id, version_id)
        
        # Hole aktive Policy
        active_policy = registry.get_active_policy(policy_id)
        assert active_policy is not None
        assert active_policy.config == {"weights": {"openai": 0.6, "claude": 0.4}}
    
    def test_list_policies(self, registry):
        """Test Policy-Liste"""
        # Erstelle mehrere Policies
        for i in range(3):
            registry.register_policy(
                name=f"Test Policy {i}",
                policy_type=PolicyType.ROUTING,
                config={"weights": {"openai": 0.6, "claude": 0.4}}
            )
        
        # Liste alle Policies
        policies = registry.list_policies()
        assert len(policies) == 3
        
        # Liste nur aktive Policies
        active_policies = registry.list_policies(status=PromptStatus.ACTIVE)
        assert len(active_policies) == 0  # Keine befördert
        
        # Liste nur Routing-Policies
        routing_policies = registry.list_policies(policy_type=PolicyType.ROUTING)
        assert len(routing_policies) == 3

class TestPromptVersion:
    """Tests für PromptVersion Dataclass"""
    
    def test_prompt_version_creation(self):
        """Test PromptVersion Erstellung"""
        version = PromptVersion(
            id="test_version",
            prompt_id="test_prompt",
            version="1.0.0",
            content="Test content",
            role="system",
            tags=["test"],
            created_at=datetime.utcnow(),
            created_by="test_user"
        )
        
        assert version.id == "test_version"
        assert version.prompt_id == "test_prompt"
        assert version.version == "1.0.0"
        assert version.content == "Test content"
        assert version.role == "system"
        assert version.tags == ["test"]
        assert version.created_by == "test_user"
        assert version.metadata is not None

class TestPrompt:
    """Tests für Prompt Dataclass"""
    
    def test_prompt_creation(self):
        """Test Prompt Erstellung"""
        prompt = Prompt(
            id="test_prompt",
            name="Test Prompt",
            description="Test description",
            current_version="v1",
            status=PromptStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert prompt.id == "test_prompt"
        assert prompt.name == "Test Prompt"
        assert prompt.description == "Test description"
        assert prompt.current_version == "v1"
        assert prompt.status == PromptStatus.DRAFT
        assert prompt.versions is not None

class TestPolicyVersion:
    """Tests für PolicyVersion Dataclass"""
    
    def test_policy_version_creation(self):
        """Test PolicyVersion Erstellung"""
        version = PolicyVersion(
            id="test_version",
            policy_id="test_policy",
            version="1.0.0",
            policy_type=PolicyType.ROUTING,
            config={"weights": {"openai": 0.6}},
            created_at=datetime.utcnow(),
            created_by="test_user"
        )
        
        assert version.id == "test_version"
        assert version.policy_id == "test_policy"
        assert version.version == "1.0.0"
        assert version.policy_type == PolicyType.ROUTING
        assert version.config == {"weights": {"openai": 0.6}}
        assert version.created_by == "test_user"
        assert version.metadata is not None

class TestPolicy:
    """Tests für Policy Dataclass"""
    
    def test_policy_creation(self):
        """Test Policy Erstellung"""
        policy = Policy(
            id="test_policy",
            name="Test Policy",
            description="Test description",
            policy_type=PolicyType.ROUTING,
            current_version="v1",
            status=PromptStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert policy.id == "test_policy"
        assert policy.name == "Test Policy"
        assert policy.description == "Test description"
        assert policy.policy_type == PolicyType.ROUTING
        assert policy.current_version == "v1"
        assert policy.status == PromptStatus.DRAFT
        assert policy.versions is not None

class TestChangelogEntry:
    """Tests für ChangelogEntry Dataclass"""
    
    def test_changelog_entry_creation(self):
        """Test ChangelogEntry Erstellung"""
        entry = ChangelogEntry(
            id="test_entry",
            timestamp=datetime.utcnow(),
            action="test_action",
            entity_type="test_entity",
            entity_id="test_id",
            version="1.0.0",
            description="Test description"
        )
        
        assert entry.id == "test_entry"
        assert entry.action == "test_action"
        assert entry.entity_type == "test_entity"
        assert entry.entity_id == "test_id"
        assert entry.version == "1.0.0"
        assert entry.description == "Test description"
        assert entry.metadata is not None
