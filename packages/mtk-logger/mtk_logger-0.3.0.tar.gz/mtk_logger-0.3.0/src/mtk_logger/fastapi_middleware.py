import uuid
import json
import os
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from starlette.responses import StreamingResponse
from fastapi import Request
import time
from .logger import get_logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Get request details
        request_id = str(uuid.uuid4())
        start_time = time.time()
        logger = get_logger(os.path.basename(__file__))

        # Extract path and method
        path = request.url.path
        method = request.method
        logger.debug(f'("Request: {request_id} - {method} {path}")')

        # Try to extract query parameters
        # Convert query_params to dict, preserving lists for repeated keys
        query_params = {}
        for key, value in request.query_params.multi_items():
            if key in query_params:
                logger.debug(f"Duplicate key '{key}' found in query parameters")
                # If the key exists but its value is not a list yet, convert it to a list
                if not isinstance(query_params[key], list):
                    query_params[key] = [query_params[key]]
                # Now we can safely append the new value
                query_params[key].append(value)
            else:
                query_params[key] = value
                logger.debug(f"Added key '{key}' to query parameters")

        # Try to extract request body (this is tricky because we can only read it once)
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # We need to read the body and then restore it for the actual endpoint
                body_bytes = await request.body()
                # Restore the request body
                request._body = body_bytes

                # Try to parse as JSON, but handle non-JSON bodies gracefully
                try:
                    body = json.loads(body_bytes.decode())
                    # For large payloads, consider truncating or summarizing
                    if isinstance(body, dict):
                        # For each list in the body, replace with count and sample
                        for key, value in body.items():
                            if isinstance(value, list) and len(value) > 5:
                                sample = value[:3]  # Take first 3 items as sample
                                body[key] = {
                                    "count": len(value),
                                    "sample": sample
                                }
                except:
                    body = {"raw_size": len(body_bytes), "note": "Non-JSON body"}
            except:
                body = {"note": "Could not read request body"}

        # Log the request
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "query_params": query_params,
            "body": body
        }

        logger.info(f"API Request: {json.dumps(log_data)}")

        # Process the request
        response = await call_next(request)

        # Read and log the response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Decode the response body
        responses = response_body.decode()

        # Try to parse the response body as JSON and count the records
        try:
            response_data = json.loads(responses)
            if isinstance(response_data, list):
                record_count = len(response_data)
            else:
                record_count = 1  # If it's not a list, assume it's a single record
        except json.JSONDecodeError:
            record_count = 0  # If the response is not JSON, set record count to 0

        # Log response details
        process_time = time.time() - start_time
        logger.info(f"Request {request_id} completed in {process_time:.4f}s with status {response.status_code} and {record_count} records")
        logger.debug(f'Request {request_id} response= {responses}')

        # Return a new StreamingResponse with the original response body
        return StreamingResponse(iter([response_body]), status_code=response.status_code, headers=dict(response.headers))
