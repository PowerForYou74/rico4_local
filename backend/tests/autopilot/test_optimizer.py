# backend/tests/autopilot/test_optimizer.py
"""
Tests für Autopilot Optimizer
"""

import pytest
from backend.autopilot.optimizer import (
    PromptOptimizer, RoutingOptimizer, MultiObjectiveOptimizer,
    PromptVariant, RoutingPolicy, OptimizationResult
)

class TestPromptOptimizer:
    """Tests für PromptOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        return PromptOptimizer()
    
    def test_generate_variants(self, optimizer):
        """Test Prompt-Varianten-Generierung"""
        base_prompt = "Du bist ein hilfreicher Assistent."
        
        variants = optimizer.generate_variants(base_prompt, num_variants=3)
        
        assert len(variants) == 3
        for variant in variants:
            assert isinstance(variant, PromptVariant)
            assert variant.id is not None
            assert variant.name is not None
            assert variant.content is not None
            assert variant.role == "system"
            assert len(variant.tags) > 0
    
    def test_apply_strategy_clarity(self, optimizer):
        """Test Klarheits-Verbesserung"""
        base_prompt = "Du bist ein Assistent."
        
        improved = optimizer._apply_strategy(base_prompt, "clarity_improvement")
        
        assert base_prompt in improved
        assert "Wichtige Hinweise" in improved
        assert len(improved) > len(base_prompt)
    
    def test_apply_strategy_constraints(self, optimizer):
        """Test Constraint-Hinzufügung"""
        base_prompt = "Du bist ein Assistent."
        
        with_constraints = optimizer._apply_strategy(base_prompt, "constraint_addition")
        
        assert base_prompt in with_constraints
        assert "Constraints" in with_constraints
        assert "Maximale Antwortlänge" in with_constraints
    
    def test_apply_strategy_role_refinement(self, optimizer):
        """Test Rollen-Verfeinerung"""
        base_prompt = "Du bist ein Assistent."
        
        refined = optimizer._apply_strategy(base_prompt, "role_refinement")
        
        assert base_prompt in refined
        assert "Experte" in refined or "Erfahrung" in refined
    
    def test_apply_strategy_context_expansion(self, optimizer):
        """Test Kontext-Erweiterung"""
        base_prompt = "Du bist ein Assistent."
        
        expanded = optimizer._apply_strategy(base_prompt, "context_expansion")
        
        assert base_prompt in expanded
        assert "Kontext" in expanded or "Ziel" in expanded
    
    def test_apply_strategy_few_shot_reordering(self, optimizer):
        """Test Few-Shot Reordering"""
        base_prompt = "Hier ist ein Beispiel: ..."
        
        reordered = optimizer._apply_strategy(base_prompt, "few_shot_reordering")
        
        assert base_prompt in reordered
        # Sollte **Beispiel:** enthalten
        assert "**Beispiel:**" in reordered or "**Example:**" in reordered

class TestRoutingOptimizer:
    """Tests für RoutingOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        return RoutingOptimizer()
    
    def test_analyze_provider_performance_empty(self, optimizer):
        """Test Provider-Performance-Analyse ohne Daten"""
        performance = optimizer.analyze_provider_performance()
        
        assert "openai" in performance
        assert "claude" in performance
        assert "perplexity" in performance
        
        for provider, metrics in performance.items():
            assert "quality_score" in metrics
            assert "latency_ms" in metrics
            assert "error_rate" in metrics
            assert "win_rate" in metrics
            assert "cost_est" in metrics
    
    def test_optimize_routing_weights(self, optimizer):
        """Test Routing-Gewichtungs-Optimierung"""
        performance = {
            "openai": {
                "quality_score": 0.8,
                "latency_ms": 2000,
                "error_rate": 0.05,
                "win_rate": 0.7,
                "cost_est": 0.01
            },
            "claude": {
                "quality_score": 0.9,
                "latency_ms": 3000,
                "error_rate": 0.03,
                "win_rate": 0.8,
                "cost_est": 0.02
            },
            "perplexity": {
                "quality_score": 0.7,
                "latency_ms": 1500,
                "error_rate": 0.08,
                "win_rate": 0.6,
                "cost_est": 0.005
            }
        }
        
        weights = optimizer.optimize_routing_weights(performance)
        
        assert "openai" in weights
        assert "claude" in weights
        assert "perplexity" in weights
        
        # Gewichtungen sollten normalisiert sein
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01
        
        # Claude sollte höchste Gewichtung haben (beste Performance)
        assert weights["claude"] >= weights["openai"]
        assert weights["claude"] >= weights["perplexity"]
    
    def test_optimize_routing_weights_with_objectives(self, optimizer):
        """Test Routing-Optimierung mit spezifischen Zielen"""
        performance = {
            "openai": {
                "quality_score": 0.8,
                "latency_ms": 2000,
                "error_rate": 0.05,
                "win_rate": 0.7,
                "cost_est": 0.01
            },
            "claude": {
                "quality_score": 0.9,
                "latency_ms": 3000,
                "error_rate": 0.03,
                "win_rate": 0.8,
                "cost_est": 0.02
            }
        }
        
        # Betone Latenz über Qualität
        objectives = {
            "quality": 0.2,
            "latency": 0.6,
            "cost": 0.1,
            "reliability": 0.1
        }
        
        weights = optimizer.optimize_routing_weights(performance, objectives)
        
        # OpenAI sollte höhere Gewichtung haben (niedrigere Latenz)
        assert weights["openai"] > weights["claude"]
    
    def test_create_routing_policy(self, optimizer):
        """Test Routing-Policy-Erstellung"""
        weights = {"openai": 0.6, "claude": 0.4}
        conditions = {"max_latency_ms": 5000}
        
        policy = optimizer.create_routing_policy(weights, conditions)
        
        assert isinstance(policy, RoutingPolicy)
        assert policy.id is not None
        assert policy.name is not None
        assert policy.weights == weights
        assert policy.conditions == conditions

class TestMultiObjectiveOptimizer:
    """Tests für MultiObjectiveOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        return MultiObjectiveOptimizer()
    
    def test_optimize_system(self, optimizer):
        """Test System-Optimierung"""
        base_prompt = "Du bist ein hilfreicher Assistent."
        
        prompt_variants, routing_policy = optimizer.optimize_system(base_prompt)
        
        assert isinstance(prompt_variants, list)
        assert len(prompt_variants) > 0
        assert isinstance(routing_policy, RoutingPolicy)
        
        for variant in prompt_variants:
            assert isinstance(variant, PromptVariant)
            assert variant.content is not None
    
    def test_optimize_system_with_objectives(self, optimizer):
        """Test System-Optimierung mit Zielen"""
        base_prompt = "Du bist ein hilfreicher Assistent."
        objectives = {
            "quality": 0.6,
            "latency": 0.2,
            "cost": 0.1,
            "reliability": 0.1
        }
        
        prompt_variants, routing_policy = optimizer.optimize_system(base_prompt, objectives)
        
        assert isinstance(prompt_variants, list)
        assert isinstance(routing_policy, RoutingPolicy)
    
    def test_evaluate_optimization(self, optimizer):
        """Test Optimierungs-Bewertung"""
        # Erstelle Test-Varianten
        variants = [
            PromptVariant(
                id="test_1",
                name="Test Variant 1",
                content="Test content 1",
                role="system"
            ),
            PromptVariant(
                id="test_2", 
                name="Test Variant 2",
                content="Test content 2",
                role="system"
            )
        ]
        
        # Erstelle Test-Policy
        policy = RoutingPolicy(
            id="test_policy",
            name="Test Policy",
            weights={"openai": 0.6, "claude": 0.4},
            conditions={"max_latency_ms": 5000}
        )
        
        results = optimizer.evaluate_optimization(variants, policy)
        
        assert "prompt_variants" in results
        assert "routing_policy" in results
        assert "overall_improvement" in results
        assert "recommendations" in results
        
        assert len(results["prompt_variants"]) == 2
        assert results["routing_policy"]["id"] == "test_policy"

class TestPromptVariant:
    """Tests für PromptVariant Dataclass"""
    
    def test_prompt_variant_creation(self):
        """Test PromptVariant Erstellung"""
        variant = PromptVariant(
            id="test_variant",
            name="Test Variant",
            content="Test content",
            role="system",
            tags=["test", "optimized"]
        )
        
        assert variant.id == "test_variant"
        assert variant.name == "Test Variant"
        assert variant.content == "Test content"
        assert variant.role == "system"
        assert variant.tags == ["test", "optimized"]
        assert variant.created_at is not None

class TestRoutingPolicy:
    """Tests für RoutingPolicy Dataclass"""
    
    def test_routing_policy_creation(self):
        """Test RoutingPolicy Erstellung"""
        policy = RoutingPolicy(
            id="test_policy",
            name="Test Policy",
            weights={"openai": 0.6, "claude": 0.4},
            conditions={"max_latency_ms": 5000}
        )
        
        assert policy.id == "test_policy"
        assert policy.name == "Test Policy"
        assert policy.weights == {"openai": 0.6, "claude": 0.4}
        assert policy.conditions == {"max_latency_ms": 5000}
        assert policy.created_at is not None

class TestOptimizationResult:
    """Tests für OptimizationResult Dataclass"""
    
    def test_optimization_result_creation(self):
        """Test OptimizationResult Erstellung"""
        result = OptimizationResult(
            type="prompt",
            variant_id="test_variant",
            improvement=0.15,
            metrics={"quality_score": 0.8, "latency_ms": 2000},
            confidence=0.9
        )
        
        assert result.type == "prompt"
        assert result.variant_id == "test_variant"
        assert result.improvement == 0.15
        assert result.metrics == {"quality_score": 0.8, "latency_ms": 2000}
        assert result.confidence == 0.9
