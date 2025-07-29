import httpx
from typing import Any, Dict, Optional, Union
from httpx import Response

from unifyops_core.logging import get_logger, add_logging_metadata
from unifyops_core.exceptions import (
    ApiClientError,
    ApiResponseError,
    NotFoundError,
)

logger = get_logger(__name__, metadata={"component": "UnifyOpsBaseHttpClient"})


class UnifyOpsBaseHttpClient:
    """
    A reusable async HTTP client with built-in logging and error handling.
    """

    def __init__(
        self,
        base_url: str,
        timeout: Union[int, float] = 10,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        add_logging_metadata(
            function="UnifyOpsBaseHttpClient.__init__",
            base_url=base_url,
            timeout=timeout,
        )
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._default_headers = default_headers or {}

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
    ) -> Any:
        """
        Make an HTTP request and return parsed JSON or None for 204.
        Raises unified exceptions for network or HTTP errors.
        """
        url = endpoint  # AsyncClient will combine with base_url
        final_headers = {**self._default_headers, **(headers or {})}
        if auth_token:
            final_headers["Authorization"] = f"Bearer {auth_token}"

        add_logging_metadata(
            function="UnifyOpsBaseHttpClient.request", method=method, endpoint=endpoint
        )
        
        # Mask sensitive data in logs
        log_json = None
        log_data = None
        if json:
            log_json = {k: ("***" if "password" in k.lower() else v) for k, v in json.items()}
        if data:
            log_data = {k: ("***" if "password" in k.lower() else v) for k, v in data.items()}
            
        logger.debug(
            "HTTP Request",
            metadata={
                "method": method,
                "url": url,
                "params": params,
                "json": log_json,
                "data": log_data,
                "headers": {k: v for k, v in final_headers.items() if k.lower() != "authorization"},
            },
        )

        try:
            response: Response = await self._client.request(
                method=method,
                url=url,
                json=json,
                data=data,
                params=params,
                headers=final_headers,
            )
        except httpx.RequestError as e:
            logger.error(
                "Network error during HTTP request",
                metadata={"error": str(e), "method": method, "url": url},
            )
            raise ApiClientError(f"Network error: {e}") from e

        return self._handle_response(response)

    def _handle_response(self, response: Response) -> Any:
        status = response.status_code

        # 2xx success
        if 200 <= status < 300:
            if status == 204:
                return None
            return response.json()

        # parse error payload
        try:
            payload = response.json()
            detail = payload.get("detail", None)
        except ValueError:
            detail = response.text

        logger.error(
            "HTTP error response",
            metadata={"status_code": status, "error": detail},
        )

        if status == 404:
            raise NotFoundError(
                message=detail or "Resource not found", resource_type="resource"
            )

        raise ApiResponseError(
            message=detail or f"Unexpected HTTP {status}",
            status_code=status,
            service="http_client",
        )

    async def close(self) -> None:
        """Explicitly close the underlying HTTP client."""
        await self._client.aclose()

    # Convenience methods for HTTP verbs
    async def get(self, endpoint: str, **kwargs) -> Any:
        """Make a GET request."""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Any:
        """Make a POST request."""
        return await self.request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Any:
        """Make a PUT request."""
        return await self.request("PUT", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Any:
        """Make a DELETE request."""
        return await self.request("DELETE", endpoint, **kwargs)
    
    async def post_form(self, endpoint: str, form_data: Dict[str, Any], **kwargs) -> Any:
        """Make a POST request with form data (for OAuth2 and similar endpoints)."""
        headers = kwargs.get("headers", {})
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        kwargs["headers"] = headers
        return await self.request("POST", endpoint, data=form_data, **kwargs)
