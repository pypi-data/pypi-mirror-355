"""
Heuristic Mesh API Client

This module provides functionality to interact with the Heuristic Mesh API.
It includes helper functions for making authenticated API calls to the mesh endpoint.
"""

import os
import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any


# Mesh API configuration
HEURIST_API_KEY = os.environ.get("HEURIST_API_KEY")
HEURIST_API_ENDPOINT = os.getenv("MESH_API_ENDPOINT", "https://sequencer-v2.heurist.xyz")

logger = logging.getLogger(__name__)


async def call_mesh_api(
    path: str, 
    method: str = "GET", 
    json: Optional[Dict[Any, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    timeout_seconds: int = 30
) -> Dict[Any, Any]:
    """
    Helper function to call the Heuristic mesh API endpoint with retry logic and timeout.
    
    Args:
        path: The API endpoint path (without base URL)
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        json: JSON payload for the request
        headers: Additional headers to include in the request
        max_retries: Maximum number of retry attempts (default: 3)
        timeout_seconds: Request timeout in seconds (default: 30)
    
    Returns:
        Dict containing the JSON response from the API
        
    Raises:
        Exception: If the API call fails or returns an error status after all retries
    """
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Create timeout configuration
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{HEURIST_API_ENDPOINT}/{path}"
                
                # Prepare headers
                request_headers = headers.copy() if headers else {}
                
                # Add API key if available
                if HEURIST_API_KEY:
                    request_headers["X-HEURIST-API-KEY"] = HEURIST_API_KEY
                
                # Make the API request
                async with session.request(
                    method, 
                    url, 
                    json=json, 
                    headers=request_headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Mesh API error (HTTP {response.status}): {error_text}"
                        )
                    
                    return await response.json()
                    
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                logger.error(f"Error calling mesh API {path} after {max_retries} attempts: {str(e)}")
                raise Exception(f"Failed to call mesh API after {max_retries} attempts: {str(e)}")
            
            # Calculate exponential backoff delay (1s, 2s, 4s, ...)
            delay = 2 ** attempt
            logger.warning(f"Attempt {attempt + 1} failed for mesh API call {path}: {str(e)}. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    
    # This should never be reached due to the loop logic, but just in case
    raise Exception(f"Failed to call mesh API after {max_retries} attempts")


async def get_mesh_api_status() -> Dict[Any, Any]:
    """
    Check the status of the Heuristic Mesh API.
    
    Returns:
        Dict containing API status information
    """
    return await call_mesh_api("health")


def get_mesh_api_config() -> Dict[str, Optional[str]]:
    """
    Get the current mesh API configuration.
    
    Returns:
        Dict containing API endpoint and key status
    """
    return {
        "endpoint": HEURIST_API_ENDPOINT,
        "api_key_configured": bool(HEURIST_API_KEY),
        "api_key": HEURIST_API_KEY[:8] + "..." if HEURIST_API_KEY else None
    } 