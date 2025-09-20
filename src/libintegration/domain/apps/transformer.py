"""Interleave and normalize two lists of strings into a single output.

This module provides a single, focused transformer function that:
  - Validates an input payload containing two equal-length lists of strings
    under the keys "list_1" and "list_2".
  - Normalizes each string (trim whitespace, collapse internal spaces).
  - Interleaves items in the order: list_1[0], list_2[0], list_1[1], list_2[1], ...
  - Produces a single uppercase, comma-and-space-separated string:
        {"output": "FIRST, OTHER, SECOND, ANOTHER, ..."}
  - Is defensive and secure by strictly validating types and sizes to prevent
    excessive memory usage and other common pitfalls.

The function does **not** mutate its input and has no side effects.

Example:
    >>> payload = {
    ...     "list_1": ["first string", "second string", "third string"],
    ...     "list_2": ["other string", "another string", "last string"],
    ... }
    >>> interleave_payload(payload)
    {'output': 'FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING'}

Design goals:
    - Single responsibility: only transform/validate; no I/O, DB, logging, or framework coupling.
    - Predictable errors: raise ValueError with clear messages on invalid inputs.
    - Maintainability/extensibility: small helpers, constants, and clear docs.

Security & robustness considerations:
    - Strict schema validation (required keys, list types, string elements).
    - Enforced size limits (items per list, item length, total output length cap).
    - No dynamic code execution or unsafe coercions; rejects non-strings.
"""

from __future__ import annotations

from pydantic import BaseModel
from logger import logger
from typing import Sequence

MAX_ITEMS: int = 100_000
MAX_ITEM_LENGTH: int = 8_192
MAX_TOTAL_OUTPUT_CHARS: int = 5_000_000


class TransformerApp(BaseModel):
    def _ensure_is_sequence_of_str(self, value: object, name: str) -> Sequence[str]:
        """Validate that value is a sequence of strings.

        Args:
            value: The value to validate.
            name: The logical name for error messages (e.g., "list_1").

        Returns:
            Sequence[str]: The validated sequence of strings.

        Raises:
            ValueError: If the value is not a sequence of strings, or violates limits.
        """
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{name} must be a list of strings.")

        if len(value) > MAX_ITEMS:
            raise ValueError(f"{name} exceeds maximum allowed items ({MAX_ITEMS}).")

        # Ensure every element is a plain string (reject None, numbers, objects, etc.)
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                raise ValueError(f"All elements of {name} must be strings (index {idx}).")

        return value

    def _collapse_whitespace(self, s: str) -> str:
        """Collapse consecutive whitespace to a single space and strip ends.

        Args:
            s: The input string.

        Returns:
            str: Normalized string with trimmed edges and single-space separation.
        """
        # Fast-path: common cases
        s = s.strip()
        if "  " not in s and "\t" not in s and "\n" not in s and "\r" not in s:
            return s

        # General normalization
        return " ".join(s.split())

    def _normalize_item(self, item: str, list_name: str, idx: int) -> str:
        """Normalize and validate a single string item.

        - Trim and collapse whitespace.
        - Enforce per-item length limits.

        Args:
            item: The raw string.
            list_name: The logical list name for error messages.
            idx: The element index for error messages.

        Returns:
            str: The normalized item.

        Raises:
            ValueError: If the normalized item exceeds length constraints.
        """
        norm = self._collapse_whitespace(item)
        if len(norm) > MAX_ITEM_LENGTH:
            error_message = f"{list_name}[{idx}] exceeds maximum allowed length ({MAX_ITEM_LENGTH})."
            logger.error(error_message)
            raise ValueError(error_message)

        return norm

    def transform(self, **kwargs):
        """Interleave two lists of strings and return a single uppercase string.

        The input must be a mapping with keys "list_1" and "list_2", each pointing
        to an equal-length list of strings. Output is a dict with a single key
        "output" containing the interleaved, uppercase, comma-and-space-separated string.

        Args:
            payload: A mapping containing:
                - "list_1": list[str]
                - "list_2": list[str]

        Returns:
            dict[str, str]: A dictionary in the form {"output": "<INTERLEAVED STRING>"}.

        Raises:
            ValueError: If the payload is missing required keys, lists are of unequal
                length, elements are not strings, or size limits are exceeded.
        """
        payload = kwargs.pop("payload")

        logger.info(f"Transofrmer App - payload : {payload}")

        if payload is None:
            error_message = "payload must not be None."
            logger.error(error_message)
            raise ValueError(error_message)

        if payload.list_1 is None or payload.list_2 is None:
            error_message = 'payload must contain keys "list_1" and "list_2".'
            logger.error(error_message)
            raise ValueError(error_message)

        list_1 = self._ensure_is_sequence_of_str(payload.list_1, "list_1")
        list_2 = self._ensure_is_sequence_of_str(payload.list_2, "list_2")

        if len(list_1) != len(list_2):
            error_message = "list_1 and list_2 must be of the same length."
            logger.error(error_message)
            raise ValueError(error_message)

        # Normalize and validate each item
        normalized_1 = [self._normalize_item(item, "list_1", i) for i, item in enumerate(list_1)]
        normalized_2 = [self._normalize_item(item, "list_2", i) for i, item in enumerate(list_2)]

        # Interleave the two lists
        interleaved: list[str] = []
        interleaved_extend = interleaved.extend
        for a, b in zip(normalized_1, normalized_2):
            interleaved_extend([a, b])

        # Join and uppercase the final output
        joined = ", ".join(interleaved)
        if len(joined) > MAX_TOTAL_OUTPUT_CHARS:
            error_message = "Final output exceeds maximum allowed length; reduce input size."
            logger.error(error_message)
            raise ValueError(error_message)

        return {"output": joined.upper()}
