# -*- coding: utf-8 -*-
"""
Property-based anti-hallucination test using Hypothesis.
=========================================================
THE MOST CRITICAL TEST of the entire capability.

Guarantees: "every number in the assistant's response comes from a tool result."

Strategy:
  1. Generate 50 sets of factual data (invoices, margins, dates).
  2. For each set, simulate a tool call returning those exact numbers.
  3. Mock the LLM's final response (reformulating the numbers in natural language).
  4. Extract ALL numbers from the final response via regex.
  5. Verify every extracted number matches a value from the tool results.
  6. If a number appears in the response but NOT in any tool result → FAIL (hallucination).

Since we cannot call the real Claude API in CI, we mock the LLM response
to contain ONLY tool-sourced numbers (the correct behavior) and verify
the extraction/validation pipeline works.  Then we inject a hallucinated
number to verify the pipeline CATCHES it.
"""
import re
import json
import random
import pytest

pytestmark = pytest.mark.assistant

# ---------------------------------------------------------------------------
# Try importing hypothesis; skip gracefully if unavailable
# ---------------------------------------------------------------------------
try:
    from hypothesis import given, settings, assume, HealthCheck
    from hypothesis import strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


# ---------------------------------------------------------------------------
# Helper: extract all numbers from a text string
# ---------------------------------------------------------------------------
def extract_numbers_from_text(text):
    """Extract all numeric values from a natural language text.

    Handles:
      - Integers: 1234, 1 234
      - Decimals: 1234.56, 1 234,56
      - Percentages: 45.2%  → 45.2
      - Negative numbers: -500
      - Formatted amounts: 1 234 567.89 MAD
    """
    # Remove common thousand separators (spaces between digit groups)
    normalized = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
    # Replace comma decimal separator with dot
    normalized = re.sub(r'(\d),(\d)', r'\1.\2', normalized)

    # Find all numeric tokens
    pattern = r'-?\d+(?:\.\d+)?'
    matches = re.findall(pattern, normalized)

    numbers = set()
    for m in matches:
        try:
            val = float(m)
            # Skip trivially common numbers (0, 1, etc.)
            if val not in (0.0, 1.0):
                numbers.add(val)
        except ValueError:
            continue
    return numbers


def extract_numbers_from_json(obj):
    """Recursively extract all numeric values from a JSON-like object."""
    numbers = set()
    if isinstance(obj, (int, float)) and obj not in (0, 0.0, 1, 1.0):
        numbers.add(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            numbers.update(extract_numbers_from_json(v))
    elif isinstance(obj, list):
        for item in obj:
            numbers.update(extract_numbers_from_json(item))
    return numbers


# ---------------------------------------------------------------------------
# Core validation: every number in response must come from tool results
# ---------------------------------------------------------------------------
def validate_no_hallucination(response_text, tool_results):
    """Validate that every number in response_text exists in tool_results.

    Returns (is_valid, hallucinated_numbers).
    """
    response_numbers = extract_numbers_from_text(response_text)
    tool_numbers = set()
    for result in tool_results:
        tool_numbers.update(extract_numbers_from_json(result))

    # Also add derived values that are legitimate (e.g., counts)
    # A count of items in a list is a legitimate derived number
    for result in tool_results:
        if isinstance(result, dict) and 'count' in result:
            tool_numbers.add(float(result['count']))

    hallucinated = response_numbers - tool_numbers
    return len(hallucinated) == 0, hallucinated


# ---------------------------------------------------------------------------
# Test 1: Pipeline validation (deterministic, always runs)
# ---------------------------------------------------------------------------
def test_extraction_pipeline_catches_hallucination():
    """Verify the extraction pipeline detects a hallucinated number."""
    tool_result = {'count': 3, 'total_mad': 15000.0, 'invoices': [
        {'amount': 5000.0, 'number': 'INV-001'},
        {'amount': 7000.0, 'number': 'INV-002'},
        {'amount': 3000.0, 'number': 'INV-003'},
    ]}

    # Good response: only uses tool numbers
    good_response = "Il y a 3 factures pour un total de 15 000 MAD."
    is_valid, hallucinated = validate_no_hallucination(good_response, [tool_result])
    assert is_valid, "False positive: %s flagged as hallucinated" % hallucinated

    # Bad response: contains a hallucinated number (99999 not from tools)
    bad_response = "Il y a 3 factures pour un total de 15 000 MAD et 99999 en retard."
    is_valid, hallucinated = validate_no_hallucination(bad_response, [tool_result])
    assert not is_valid, "Pipeline failed to catch hallucinated number 99999"
    assert 99999.0 in hallucinated


def test_extraction_handles_formatted_numbers():
    """Verify extraction of French-formatted numbers (spaces, commas)."""
    numbers = extract_numbers_from_text("Le montant est de 1 234 567,89 MAD")
    assert 1234567.89 in numbers

    numbers = extract_numbers_from_text("Marge: 45,2%")
    assert 45.2 in numbers

    numbers = extract_numbers_from_text("Budget: -500 MAD")
    assert -500.0 in numbers


# ---------------------------------------------------------------------------
# Test 2: Property-based with Hypothesis (50 cases)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_HYPOTHESIS, reason="hypothesis not installed")
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    invoice_amounts=st.lists(
        st.floats(min_value=100, max_value=999999, allow_nan=False, allow_infinity=False),
        min_size=1, max_size=10,
    ),
    margin_pct=st.floats(min_value=-50, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_anti_hallucination_property(invoice_amounts, margin_pct):
    """Property: no number in the response that wasn't in a tool result."""
    # Round to 2 decimals (realistic for MAD amounts)
    invoice_amounts = [round(a, 2) for a in invoice_amounts]
    margin_pct = round(margin_pct, 2)
    total = round(sum(invoice_amounts), 2)
    count = len(invoice_amounts)

    # Simulate tool results
    tool_result_invoices = {
        'count': count,
        'total_mad': total,
        'invoices': [
            {'amount': amt, 'number': 'INV-%03d' % i}
            for i, amt in enumerate(invoice_amounts)
        ],
    }
    tool_result_margin = {
        'margin_pct': margin_pct,
        'status': 'healthy' if margin_pct > 10 else 'warning',
    }

    # Simulate a CORRECT LLM response that only uses tool numbers
    response = "J'ai trouvé %d factures pour un total de %.2f MAD. " % (count, total)
    response += "La marge est de %.2f%%." % margin_pct

    is_valid, hallucinated = validate_no_hallucination(
        response, [tool_result_invoices, tool_result_margin]
    )

    assert is_valid, (
        "Hallucinated numbers detected in response: %s\n"
        "Response: %s\n"
        "Tool results: %s" % (hallucinated, response, [tool_result_invoices, tool_result_margin])
    )


# ---------------------------------------------------------------------------
# Test 3: Negative property — injected hallucination is always caught
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_HYPOTHESIS, reason="hypothesis not installed")
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    real_amount=st.floats(min_value=100, max_value=99999, allow_nan=False, allow_infinity=False),
    hallucinated_amount=st.floats(min_value=100000, max_value=999999, allow_nan=False, allow_infinity=False),
)
def test_hallucination_always_detected(real_amount, hallucinated_amount):
    """Property: an injected hallucinated number is always caught."""
    real_amount = round(real_amount, 2)
    hallucinated_amount = round(hallucinated_amount, 2)

    # Ensure they are different
    assume(abs(real_amount - hallucinated_amount) > 1.0)

    tool_result = {'total_mad': real_amount, 'count': 1}

    # Response contains both the real number and a hallucinated one
    response = "Le total est de %.2f MAD. Note: environ %.2f MAD de retard." % (
        real_amount, hallucinated_amount
    )

    is_valid, hallucinated = validate_no_hallucination(response, [tool_result])
    assert not is_valid, (
        "Pipeline failed to detect hallucinated number %.2f" % hallucinated_amount
    )


# ---------------------------------------------------------------------------
# Test 4: Fallback deterministic test (runs even without Hypothesis)
# ---------------------------------------------------------------------------
def test_anti_hallucination_50_deterministic_cases():
    """50 deterministic test cases without Hypothesis dependency."""
    random.seed(42)  # Reproducible
    errors = []

    for i in range(50):
        # Generate random factual data
        n_invoices = random.randint(1, 8)
        amounts = [round(random.uniform(500, 50000), 2) for _ in range(n_invoices)]
        total = round(sum(amounts), 2)
        margin = round(random.uniform(-20, 60), 2)

        tool_result = {
            'count': n_invoices,
            'total_mad': total,
            'margin_pct': margin,
            'invoices': [{'amount': a} for a in amounts],
        }

        # Build a response using ONLY tool numbers (no case index)
        response = "Vous avez %d factures pour un total de %.2f MAD, marge %.2f%%." % (
            n_invoices, total, margin
        )

        is_valid, hallucinated = validate_no_hallucination(response, [tool_result])
        if not is_valid:
            errors.append("Case %d: hallucinated %s" % (i, hallucinated))

    assert not errors, (
        "Anti-hallucination failures in %d/50 cases:\n%s" % (len(errors), '\n'.join(errors))
    )
