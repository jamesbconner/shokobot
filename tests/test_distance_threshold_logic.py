"""Test to verify distance threshold logic is correct."""

import pytest


def test_distance_threshold_logic():
    """Verify that distance threshold logic works correctly.
    
    With distance scores (lower = better):
    - Best score should be the MINIMUM
    - Good results should be BELOW threshold
    """
    # Simulate distance scores (lower = better)
    results = [
        ("doc1", 0.2),  # Excellent match
        ("doc2", 0.5),  # Good match
        ("doc3", 0.8),  # Moderate match
        ("doc4", 1.2),  # Poor match
    ]
    
    # Get best (minimum) score
    best_score = min(score for _, score in results)
    assert best_score == 0.2, "Best score should be the minimum (lowest)"
    
    # Test threshold logic
    threshold = 0.7
    
    # Good results should be BELOW threshold (<=)
    score_met = best_score <= threshold
    assert score_met is True, f"Best score {best_score} should be <= threshold {threshold}"
    
    # Test with poor results
    poor_results = [
        ("doc1", 1.5),  # Poor match
        ("doc2", 1.8),  # Poor match
    ]
    
    poor_best = min(score for _, score in poor_results)
    poor_score_met = poor_best <= threshold
    assert poor_score_met is False, f"Poor score {poor_best} should be > threshold {threshold}"


def test_filter_by_threshold():
    """Verify filtering by threshold works correctly."""
    results = [
        ("doc1", 0.2),  # Keep
        ("doc2", 0.5),  # Keep
        ("doc3", 0.8),  # Reject
        ("doc4", 1.2),  # Reject
    ]
    
    threshold = 0.6
    
    # Filter: keep scores <= threshold (lower = better)
    filtered = [(doc, score) for doc, score in results if score <= threshold]
    
    assert len(filtered) == 2, "Should keep 2 results with scores <= 0.6"
    assert filtered[0][1] == 0.2, "First result should have score 0.2"
    assert filtered[1][1] == 0.5, "Second result should have score 0.5"


def test_mcp_fallback_logic():
    """Verify MCP fallback logic with distance scores."""
    # Scenario 1: Good results (should NOT trigger MCP)
    good_results = [("doc1", 0.3), ("doc2", 0.4)]
    best_score = min(score for _, score in good_results)
    threshold = 0.7
    count_threshold = 2
    
    count_met = len(good_results) >= count_threshold
    score_met = best_score <= threshold
    
    should_skip_mcp = count_met and score_met
    assert should_skip_mcp is True, "Should skip MCP with good results"
    
    # Scenario 2: Poor results (should trigger MCP)
    poor_results = [("doc1", 1.5), ("doc2", 1.8)]
    poor_best = min(score for _, score in poor_results)
    
    poor_count_met = len(poor_results) >= count_threshold
    poor_score_met = poor_best <= threshold
    
    should_trigger_mcp = not (poor_count_met and poor_score_met)
    assert should_trigger_mcp is True, "Should trigger MCP with poor results"
    
    # Scenario 3: Few results (should trigger MCP)
    few_results = [("doc1", 0.3)]
    few_best = min(score for _, score in few_results)
    
    few_count_met = len(few_results) >= count_threshold
    few_score_met = few_best <= threshold
    
    should_trigger_mcp_few = not (few_count_met and few_score_met)
    assert should_trigger_mcp_few is True, "Should trigger MCP with too few results"


if __name__ == "__main__":
    test_distance_threshold_logic()
    test_filter_by_threshold()
    test_mcp_fallback_logic()
    print("✅ All distance threshold logic tests passed!")
