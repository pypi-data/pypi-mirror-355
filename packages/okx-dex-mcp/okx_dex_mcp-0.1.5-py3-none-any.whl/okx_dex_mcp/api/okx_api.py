"""
OKX API client utilities for authentication and request handling.
"""

import httpx
import base64
import hmac
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..utils.constants import (
    OKX_API_BASE, OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE, 
    OKX_PROJECT_ID, OKX_SANDBOX, USER_AGENT
)


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    timeout: float = 30.0


def create_okx_signature(timestamp: str, method: str, request_path: str, body: str = "") -> str:
    """Create OKX API signature using HMAC-SHA256."""
    if not OKX_SECRET_KEY:
        return ""
    
    # Ensure body is properly formatted JSON string if it's not empty
    if body and isinstance(body, (dict, list)):
        body = json.dumps(body, separators=(',', ':'))
    
    message = timestamp + method + request_path + body
    signature = base64.b64encode(
        hmac.new(
            OKX_SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    return signature


def get_okx_headers(method: str, request_path: str, body: str = "") -> Dict[str, str]:
    """Generate OKX API headers with authentication."""
    # Generate current timestamp in the exact format OKX expects (ISO format with milliseconds)
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Add authentication headers if API credentials are available
    if OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE:
        signature = create_okx_signature(timestamp, method, request_path, body)
        headers.update({
            "OK-ACCESS-KEY": OKX_API_KEY,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE
        })
        
        # Add project ID if available
        if OKX_PROJECT_ID:
            headers["OK-ACCESS-PROJECT"] = OKX_PROJECT_ID
        
        if OKX_SANDBOX:
            headers["x-simulated-trading"] = "1"
    
    return headers


def _should_retry(status_code: int, exception: Exception = None) -> bool:
    """Determine if a request should be retried based on status code or exception."""
    # Retry on server errors (5xx) and specific client errors
    if status_code:
        return status_code >= 500 or status_code in [429, 408, 502, 503, 504]
    
    # Retry on specific exceptions
    if exception:
        return isinstance(exception, (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
        ))
    
    return False


async def _make_single_request(
    client: httpx.AsyncClient, 
    url: str, 
    method: str, 
    headers: Dict[str, str], 
    body_str: str,
    timeout: float
) -> httpx.Response:
    """Make a single HTTP request."""
    if method == "GET":
        return await client.get(url, headers=headers, timeout=timeout)
    else:
        return await client.request(
            method, 
            url, 
            headers=headers, 
            content=body_str if body_str else None, 
            timeout=timeout
        )


async def make_okx_request(
    url: str, 
    method: str = "GET", 
    body: Any = None,
    retry_config: RetryConfig = None
) -> Optional[Dict[str, Any]]:
    """Make a request to the OKX API with proper authentication, retry logic, and timeout handling."""
    if retry_config is None:
        retry_config = RetryConfig()
    
    # Extract request path from full URL
    request_path = url.replace(OKX_API_BASE, "")
    
    # Convert body to JSON string if it's a dict/list
    body_str = ""
    if body is not None:
        if isinstance(body, (dict, list)):
            body_str = json.dumps(body, separators=(',', ':'))
        else:
            body_str = str(body)
    
    last_exception = None
    
    for attempt in range(retry_config.max_retries + 1):  # +1 for initial attempt
        try:
            # Generate fresh headers for each attempt (includes new timestamp)
            headers = get_okx_headers(method, request_path, body_str)
            
            async with httpx.AsyncClient() as client:
                response = await _make_single_request(
                    client, url, method, headers, body_str, retry_config.timeout
                )
                
                # Check if we should retry based on status code
                if _should_retry(response.status_code):
                    if attempt < retry_config.max_retries:
                        delay = min(
                            retry_config.base_delay * (retry_config.backoff_factor ** attempt),
                            retry_config.max_delay
                        )
                        print(f"OKX API request failed with status {response.status_code}, retrying in {delay:.2f}s (attempt {attempt + 1}/{retry_config.max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"OKX API request failed after {retry_config.max_retries + 1} attempts with status {response.status_code}")
                        response.raise_for_status()
                
                # Success case
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            last_exception = e
            
            # Check if we should retry based on exception type
            if _should_retry(None, e) and attempt < retry_config.max_retries:
                delay = min(
                    retry_config.base_delay * (retry_config.backoff_factor ** attempt),
                    retry_config.max_delay
                )
                print(f"OKX API request failed with {type(e).__name__}: {e}, retrying in {delay:.2f}s (attempt {attempt + 1}/{retry_config.max_retries + 1})")
                await asyncio.sleep(delay)
                continue
            else:
                # Either non-retryable error or max retries exceeded
                print(f"OKX API Error after {attempt + 1} attempts: {e}")
                break
    
    # If we get here, all retries failed
    return None


# Helper function for common retry configurations
def get_retry_config(
    max_retries: int = 3,
    timeout: float = 30.0,
    base_delay: float = 1.0
) -> RetryConfig:
    """Create a retry configuration with common settings."""
    return RetryConfig(
        max_retries=max_retries,
        timeout=timeout,
        base_delay=base_delay
    ) 