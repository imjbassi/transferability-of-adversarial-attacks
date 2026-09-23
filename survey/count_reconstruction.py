"""Recover possible integer numerators under explicit nearest-unit rounding.

This does not establish the denominator or prove that a rate is not an average.
Only use after checking those facts in the source protocol.
"""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from rounding_bounds import interval

def count_candidates(displayed_percent, denominator):
    if isinstance(denominator, bool) or not isinstance(denominator, int) or denominator <= 0:
        raise ValueError("A known positive integer denominator is required")
    low, high = interval(displayed_percent)
    lower_count = int((low * denominator / Decimal(100)).to_integral_value(rounding=ROUND_CEILING))
    upper_count = int((high * denominator / Decimal(100)).to_integral_value(rounding=ROUND_FLOOR))
    count = max(0, upper_count - lower_count + 1)
    return {
        "denominator": denominator,
        "displayed_percent": displayed_percent,
        "minimum_numerator": lower_count if count else None,
        "maximum_numerator": upper_count if count else None,
        "candidate_count": count,
        "unique_numerator": lower_count if count == 1 else None,
        "assumption": "Single empirical proportion, known denominator, nearest displayed unit; rounding ties included conservatively."
    }
