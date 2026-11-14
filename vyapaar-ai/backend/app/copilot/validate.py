"""backend/app/copilot/validate.py
Number validator per docs/02 section 5.
Extracts every number from the answer (strips commas, Rs, %, handles lakh/crore).
Verifies that each number appears in tool results within +-0.5% or is a date/ordinal.
If validation fails, signals failure so caller can discard LLM text and use deterministic template.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import re

# Ordinals, standard days, years, and small counts
ALLOWED_DATES_AND_ORDINALS = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    14, 15, 21, 28, 30, 45, 60, 90,
    2024, 2025, 2026, 2027,
}


def extract_numbers_from_text(text: str) -> List[float]:
    """Extracts numbers from natural language text:
    - Handles 'Rs 14,32,103', '14.3 lakh', '1.5 crore', '10.4%', '+8.1%', '4.1x', etc.
    """
    pattern = r'(?:Rs\.?|₹)?\s*([+-]?[0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(lakh|lac|crore|cr)?%?'
    numbers = []

    for m in re.finditer(pattern, text, re.IGNORECASE):
        num_str = m.group(1).replace(',', '')
        scale_str = m.group(2)
        try:
            val = float(num_str)
            if scale_str:
                scale_lower = scale_str.lower()
                if scale_lower in ('lakh', 'lac'):
                    val *= 100000.0
                elif scale_lower in ('crore', 'cr'):
                    val *= 10000000.0
            numbers.append(val)
        except ValueError:
            pass

    return numbers


def collect_numbers_from_data(data: Any, target_set: Set[float]) -> None:
    """Recursively traverses data structures and collects all numeric values."""
    if isinstance(data, (int, float)):
        target_set.add(float(data))
    elif isinstance(data, dict):
        for k, v in data.items():
            collect_numbers_from_data(v, target_set)
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            collect_numbers_from_data(item, target_set)
    elif isinstance(data, str):
        # Extract potential numbers embedded in string values
        for n in extract_numbers_from_text(data):
            target_set.add(n)


def is_number_grounded(
    num: float,
    valid_numbers: Set[float],
    allowed_tolerance: float = 0.005,
) -> bool:
    """Checks if num is grounded in valid_numbers within relative tolerance (or 0.5 absolute),
    or matches a recognized date/ordinal.
    """
    int_val = round(num)
    if abs(num - int_val) < 1e-4 and int_val in ALLOWED_DATES_AND_ORDINALS:
        return True

    for v in valid_numbers:
        tol = max(allowed_tolerance * abs(v), 0.5)
        if abs(num - v) <= tol:
            return True

    return False


def validate_answer(
    answer: str,
    tool_results: List[Dict[str, Any]],
    tool_args: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[bool, List[float]]:
    """Validates that all numbers in answer exist in tool_results or tool_args within +-0.5%.
    Returns (is_valid, unverified_numbers).
    """
    text_numbers = extract_numbers_from_text(answer)
    if not text_numbers:
        return True, []

    valid_numbers: Set[float] = set()
    for tr in tool_results:
        collect_numbers_from_data(tr.get("data"), valid_numbers)
        collect_numbers_from_data(tr.get("meta"), valid_numbers)

    if tool_args:
        for arg_dict in tool_args:
            collect_numbers_from_data(arg_dict, valid_numbers)

    unverified = []
    for n in text_numbers:
        if not is_number_grounded(n, valid_numbers):
            unverified.append(n)

    is_valid = len(unverified) == 0
    return is_valid, unverified
