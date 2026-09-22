"""REST API source ingestion for the Enterprise Data Pipeline.

This module retrieves source data from a REST API endpoint using
httpx. It does NOT perform business validation — that is the
responsibility of later pipeline stages.

The ingestion layer handles:
  - HTTP connection and timeout failures (source-access failures)
  - HTTP 4xx / 5xx responses (source-access failures)
  - JSON parsing of a valid response
  - Malformed JSON response (parsing failure)

It does NOT decide whether the retrieved records are business-valid.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Default timeout (seconds) for all HTTP requests from the ingestion layer.
# Prevents the pipeline from hanging indefinitely on an unresponsive source.
DEFAULT_TIMEOUT = 10.0


def ingest_rest(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve source data from a REST API endpoint.

    Sends a GET request to `url` and returns the JSON response body as a
    list of dictionaries. The caller is responsible for providing an
    appropriate URL (and optional headers) — no credentials are hardcoded
    here.

    Args:
        url:     Full URL of the REST endpoint to call.
        timeout: Request timeout in seconds (default: 10).
        headers: Optional HTTP headers (e.g. Authorization). These must be
                 provided by the caller from environment variables, never
                 hardcoded.

    Returns:
        List of dictionaries parsed from the JSON response body.

    Raises:
        ConnectionError:  If the server cannot be reached or the request
                          times out.
        RuntimeError:     If the server returns an HTTP 4xx or 5xx status.
        ValueError:       If the response body is not valid JSON or is not
                          a JSON array.
    """
    logger.info("REST ingestion starting | url=%s", url)

    try:
        response = httpx.get(url, timeout=timeout, headers=headers or {})
    except httpx.TimeoutException as e:
        logger.error("REST request timed out: %s", e)
        raise ConnectionError(f"REST source timed out: {url}") from e
    except httpx.RequestError as e:
        # Covers all network-level errors: DNS failure, connection refused, etc.
        logger.error("REST connection failed: %s", e)
        raise ConnectionError(f"Cannot reach REST source: {url} — {e}") from e

    # Surface HTTP error status codes as ingestion failures.
    if response.status_code >= 400:
        logger.error(
            "REST source returned error status | url=%s status=%d",
            url,
            response.status_code,
        )
        raise RuntimeError(
            f"REST source returned HTTP {response.status_code} for {url}"
        )

    # Parse the response body.
    try:
        data = response.json()
    except Exception as e:
        logger.error("REST response is not valid JSON: %s", e)
        raise ValueError(f"REST source returned non-JSON response: {url}") from e

    if not isinstance(data, list):
        raise ValueError(
            f"REST source returned unexpected type {type(data).__name__}, "
            f"expected a JSON array: {url}"
        )

    logger.info("REST ingestion complete | url=%s records=%d", url, len(data))
    return data
