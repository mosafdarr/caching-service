"""Documentation strings for cache API endpoints.

This module centralizes human-readable summaries and descriptions
used in FastAPI route decorators, ensuring consistency across the API.

Attributes:
    summary (str): Summary text for retrieving a cached payload by ID.
    descriptions (str): Detailed description for the GET payload endpoint.
    create_payload_summary (str): Summary text for creating a new cache payload.
    create_payload_descriptions (str): Detailed description for the POST payload endpoint.
"""

summary = """Cache Payload"""
descriptions = """Get Cached Payload by ID"""

create_payload_summary = """Create Cache Payload"""
create_payload_descriptions = """Create a new cache payload by providing two lists of strings. The lists must be of the same length. The service will interleave the strings from both lists to generate a single output string and return a unique identifier for the created payload."""
