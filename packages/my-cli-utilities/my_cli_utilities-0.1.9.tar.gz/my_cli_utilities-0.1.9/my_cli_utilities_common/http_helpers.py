# my_cli_utilities_common/http_helpers.py
import httpx
import json
import asyncio
import sys
import os

import logging

# Initialize logger
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger('http_helpers')

def log_error(message: str, request_url: str = None, response_text: str = None):
    '''Helper function to log formatted error messages.'''
    error_msg = f"{message}"
    if request_url:
        error_msg += f" (URL: {request_url})"
    logger.error(error_msg)
    if response_text:
        # Truncate long responses for readability
        truncated_response = response_text[:500] + "..." if len(response_text) > 500 else response_text
        logger.debug(f"Raw response: {truncated_response}")

def make_sync_request(url: str, params: dict = None, method: str = "GET"):
    '''Makes a synchronous HTTP request and handles common errors.'''
    try:
        with httpx.Client() as client:
            if method.upper() == "GET":
                response = client.get(url, params=params)
            # Example for POST, can be expanded
            # elif method.upper() == "POST":
            #     response = client.post(url, json=params)
            else:
                log_error(f"Unsupported HTTP method: {method}", url)
                return None
            
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            return response.json()
    except httpx.HTTPStatusError as exc:
        log_error(f"HTTP error {exc.response.status_code}", str(exc.request.url), exc.response.text)
    except httpx.RequestError as exc:
        request_url_for_error = str(exc.request.url) if hasattr(exc.request, 'url') and exc.request.url else url
        log_error(f"Request error: {type(exc).__name__}", request_url_for_error)
    except json.JSONDecodeError:
        log_error("Failed to decode JSON response", url)
    return None

async def make_async_request(url: str, params: dict = None, method: str = "GET"):
    '''Makes an asynchronous HTTP request and handles common errors.'''
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, params=params)
            # Example for POST, can be expanded
            # elif method.upper() == "POST":
            #     response = await client.post(url, json=params)
            else:
                log_error(f"Unsupported HTTP method: {method}", url)
                return None

            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        log_error(f"HTTP error {exc.response.status_code}", str(exc.request.url), exc.response.text)
    except httpx.RequestError as exc:
        request_url_for_error = str(exc.request.url) if hasattr(exc.request, 'url') and exc.request.url else url
        log_error(f"Request error: {type(exc).__name__}", request_url_for_error)
    except json.JSONDecodeError:
        log_error("Failed to decode JSON response", url)
    return None

if __name__ == '__main__':
    # Example usage (synchronous)
    logger.info("Testing sync request...")
    sync_data = make_sync_request("https://jsonplaceholder.typicode.com/todos/1")
    if sync_data:
        logger.info("Sync data: " + json.dumps(sync_data, indent=2))
    else:
        logger.error("Sync request failed.")

    # Example usage (asynchronous)
    async def main_async_test():
        logger.info("Testing async request...")
        async_data = await make_async_request("https://jsonplaceholder.typicode.com/posts/1")
        if async_data:
            logger.info("Async data: " + json.dumps(async_data, indent=2))
        else:
            logger.error("Async request failed.")

    asyncio.run(main_async_test()) 