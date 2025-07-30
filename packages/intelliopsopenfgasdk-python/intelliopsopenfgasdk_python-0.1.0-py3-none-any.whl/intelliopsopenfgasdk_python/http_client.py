from typing import Any, Dict, Optional
import httpx


class HttpClient:
    """
    HttpClient provides synchronous and asynchronous HTTP methods using httpx.

    Args:
        base_url (Optional[str]): The base URL for requests. Defaults to empty string.
        headers (Optional[Dict[str, str]]): Default headers to include in requests.
        timeout (Optional[float]): Timeout for requests in seconds. Defaults to 10.0.

    Methods:
        get(url, params=None, **kwargs):
            Perform a synchronous HTTP GET request.
        post(url, data=None, json=None, **kwargs):
            Perform a synchronous HTTP POST request.
        async_get(url, params=None, **kwargs):
            Perform an asynchronous HTTP GET request.
        async_post(url, data=None, json=None, **kwargs):
            Perform an asynchronous HTTP POST request.
        close():
            Close the synchronous client.
        aclose():
            Close the asynchronous client.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = 10.0,
    ):
        self.base_url = base_url or ""
        self.headers = headers or {}
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )
        self.async_client = httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        merged_headers = {**self.headers, **(headers or {})}
        return self.client.get(url, params=params, headers=merged_headers, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        merged_headers = {**self.headers, **(headers or {})}
        return self.client.post(
            url, data=data, json=json, headers=merged_headers, **kwargs
        )

    async def async_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        merged_headers = {**self.headers, **(headers or {})}
        return await self.async_client.get(
            url, params=params, headers=merged_headers, **kwargs
        )

    async def async_post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        merged_headers = {**self.headers, **(headers or {})}
        return await self.async_client.post(
            url, data=data, json=json, headers=merged_headers, **kwargs
        )

    def close(self):
        self.client.close()

    async def aclose(self):
        await self.async_client.aclose()
