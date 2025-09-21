"""Minimal asynchronous CLI for the Caching Service.

This script provides a small, dependency-light command-line interface to:
  1) POST a payload to the caching service to obtain a deterministic `payload_id`.
  2) GET the cached, transformed output using that `payload_id`.
It can repeat the POST+GET cycle multiple times to observe idempotency and timings.

Usage:
    # Inline JSON payload (takes precedence over --input)
    python cache_cli_simple_async.py -j '{"list_1":["a","b"],"list_2":["c","d"]}'

    # Read from file and write results to file (repeat 3 iterations)
    python cache_cli_simple_async.py -i payload.json -o result.json -r 3

    # Read payload from stdin and write results to stdout
    cat payload.json | python cache_cli_simple_async.py -i - -o -

Notes:
    - This CLI is intentionally minimal: no Pydantic models and no settings library.
    - The service is expected to be available at `--host` (default http://localhost:8000).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import httpx

from typing import Any, Dict, List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser for CLI arguments.
    """
    parser = argparse.ArgumentParser(description="Simple async CLI for caching service")

    parser.add_argument(
        "-H",
        "--host",
        default="http://localhost:8000",
        help="Base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "-r",
        "--repeat",
        type=int,
        default=1,
        help="Number of POST+GET iterations (default: 1)",
    )
    parser.add_argument(
        "-i",
        "--input",
        help='Input file path or "-" for stdin (JSON)',
    )
    parser.add_argument(
        "-j",
        "--json",
        help="Inline JSON payload string (takes precedence over --input)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help='Output file path or "-" for stdout (writes all results)',
    )

    return parser


def read_stdin() -> str:
    """Read all text from standard input.

    Returns:
        str: The text read from stdin (empty string if no input).
    """
    return sys.stdin.read() or ""


def read_file(path: str) -> str:
    """Read all text from a file.

    Args:
        path: The file system path to read.

    Returns:
        str: File contents as text.
    """
    with open(path, "r", encoding="utf-8") as file_handle:
        return file_handle.read()


def load_payload(args: argparse.Namespace) -> Dict[str, Any]:
    """Load a JSON payload from CLI args (inline JSON, file, or stdin).

    Precedence:
        1) --json inline string
        2) --input path (or "-" for stdin)

    Args:
        args: Parsed CLI arguments.

    Returns:
        dict: The parsed JSON payload.

    Raises:
        SystemExit: If no input is provided or JSON is invalid.
    """
    raw_text: Optional[str] = None

    if args.json:
        raw_text = args.json
    elif args.input:
        if args.input.strip() == "-":
            raw_text = read_stdin()
        else:
            raw_text = read_file(args.input)
    else:
        raise SystemExit("No input provided. Use --json or --input (or -i - for stdin).")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON input: {exc}") from exc


def write_output(output_arg: Optional[str], data: Any) -> None:
    """Write a JSON result to a file or stdout.

    Args:
        output_arg: Output target path, "-" for stdout, or None to skip writing.
        data: JSON-serializable data to write.
    """
    if not output_arg:
        return

    text = json.dumps(data, indent=2, ensure_ascii=False)
    if output_arg.strip() == "-":
        print(text)
    else:
        with open(output_arg, "w", encoding="utf-8") as file_handle:
            file_handle.write(text + "\n")


async def do_iteration(
    client: httpx.AsyncClient, payload: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
    """Perform one POST+GET cycle and collect timings.

    Steps:
        1) POST /payload with the provided payload body.
        2) Extract `payload_id` from the response (accepts a few common shapes).
        3) GET /payload/{payload_id} to retrieve the transformed output.

    Args:
        client: An initialized `httpx.AsyncClient`.
        payload: The JSON payload to send to the service.

    Returns:
        tuple:
            payload_id (str): The identifier returned by POST.
            get_json (dict): The JSON body returned by GET.
            timings (dict[str, float]): Millisecond timings for POST, GET, and total.

    Raises:
        RuntimeError: If a `payload_id` cannot be extracted from the POST response.
    """
    iteration_started_ms = time.perf_counter()

    post_started_ms = time.perf_counter()
    post_response = await client.post("/payload", json=payload)
    post_response.raise_for_status()
    post_json = post_response.json()
    post_elapsed_ms = (time.perf_counter() - post_started_ms) * 1000.0

    payload_id: Optional[str] = None
    if isinstance(post_json, dict):
        for key in ("payload_id", "id", "identifier", "uuid"):
            if key in post_json:
                payload_id = str(post_json[key])
                break
        if payload_id is None and len(post_json) == 1:
            payload_id = str(next(iter(post_json.values())))
    elif isinstance(post_json, str):
        payload_id = post_json

    if payload_id is None:
        raise RuntimeError(
            f"Could not extract payload id from POST response: {post_json}"
        )

    get_started_ms = time.perf_counter()
    get_response = await client.get(f"/payload/{payload_id}")
    get_response.raise_for_status()
    get_json = get_response.json()
    get_elapsed_ms = (time.perf_counter() - get_started_ms) * 1000.0

    total_elapsed_ms = (time.perf_counter() - iteration_started_ms) * 1000.0
    timings = {
        "post_ms": round(post_elapsed_ms, 3),
        "get_ms": round(get_elapsed_ms, 3),
        "total_ms": round(total_elapsed_ms, 3),
    }

    return payload_id, get_json, timings


async def run(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute the requested number of POST+GET iterations.

    Args:
        args: Parsed CLI arguments.

    Returns:
        dict: Aggregated results including payload IDs, outputs, and per-iteration timings.
    """
    seen_payload_ids: set[str] = set()
    outputs_by_id: Dict[str, Dict[str, Any]] = {}
    iteration_timings: List[Dict[str, float]] = []

    payload = load_payload(args)
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(
        base_url=args.host.rstrip("/"),
        timeout=timeout,
    ) as client:
        for _ in range(max(1, args.repeat or 1)):
            payload_id, get_json, timings = await do_iteration(client, payload)
            seen_payload_ids.add(payload_id)

            # Keep the first observed output per id
            outputs_by_id.setdefault(payload_id, get_json)
            iteration_timings.append(timings)

    total_ms = sum(item["total_ms"] for item in iteration_timings)
    avg_total_ms = total_ms / max(1, len(iteration_timings))
    outputs_list = [outputs_by_id[pid] for pid in seen_payload_ids]

    result: Dict[str, Any] = {
        "host": args.host,
        "repeat": args.repeat,
        "payload_ids": seen_payload_ids,  # Note: a set is not JSON-serializable.
        "outputs": outputs_list,
        "timings": {
            "total_ms": round(total_ms, 3),
            "avg_total_ms_per_iteration": round(avg_total_ms, 3),
            "iterations": iteration_timings,
        },
    }

    write_output(args.output, result)
    return result


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional list of command-line arguments. If None, uses sys.argv.

    Returns:
        int: Process exit code (0 on success, non-zero on failure).
    """
    parser = build_parser()
    ns = parser.parse_args(argv)

    try:
        result = asyncio.run(run(ns))
    except (httpx.HTTPError, RuntimeError, SystemExit) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2

    sys.stderr.write(
        "=== cache-cli summary ===\n"
        f"Host: {ns.host}\n"
        f"Repeat: {ns.repeat}\n"
        f"Unique Payload IDs: {', '.join(result['payload_ids'])}\n"
        f"Total time: {result['timings']['total_ms']:.3f} ms  |  "
        f"Avg/iter: {result['timings']['avg_total_ms_per_iteration']:.3f} ms\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
