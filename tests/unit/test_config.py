"""Unit tests for core/config.py"""

import pytest
from core.config import estimate_cost, estimate_embedding_cost, get_pricing


def test_estimate_cost_openai_gpt4o_mini():
    cost = estimate_cost("openai", "gpt-4o-mini", input_tokens=1000, output_tokens=500)
    assert cost > 0
    # input: 1000/1000 * 0.00015 = 0.00015, output: 500/1000 * 0.00060 = 0.00030
    assert cost == pytest.approx(0.00045, abs=1e-8)


def test_estimate_cost_unknown_provider():
    cost = estimate_cost("unknown", "unknown-model", input_tokens=1000, output_tokens=500)
    assert cost == 0.0


def test_estimate_embedding_cost():
    cost = estimate_embedding_cost("openai", "text-embedding-3-small", total_tokens=1000)
    assert cost == pytest.approx(0.00002, abs=1e-8)


def test_get_pricing_found():
    pricing = get_pricing("openai", "gpt-4o-mini")
    assert pricing is not None
    assert "input" in pricing


def test_get_pricing_not_found():
    pricing = get_pricing("nonexistent", "model")
    assert pricing is None
