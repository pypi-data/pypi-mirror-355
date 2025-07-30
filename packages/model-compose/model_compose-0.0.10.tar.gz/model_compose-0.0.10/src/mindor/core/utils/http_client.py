from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, AsyncIterator, Any
from .http_headers import parse_options_header, get_header_value
from .resources import StreamResource

from urllib.parse import urlencode
import aiohttp, json

class HttpStreamResource(StreamResource):
    def __init__(self, session: aiohttp.ClientSession, stream: aiohttp.StreamReader, content_type: Optional[str], filename: Optional[str]):
        super().__init__(content_type, filename)

        self.session: aiohttp.ClientSession = session
        self.stream: aiohttp.StreamReader = stream

    def get_stream(self):
        return self.stream
    
    async def close(self):
        await self.session.close()

    async def _iterate_stream(self) -> AsyncIterator[bytes]:
        _, buffer_size = self.stream.get_read_buffer_limits()
        chunk_size = buffer_size or 65536

        while not self.stream.at_eof():
            chunk = await self.stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

class HttpClient:
    async def request(self, url: str, method: str, params: Optional[Dict[str, Any]], body: Optional[Any], headers: Optional[Dict[str, str]]) -> Any:
        session = aiohttp.ClientSession()
        try:
            response = await session.request(                
                method,
                url,
                params=params,
                data=self._serialize_request_body(body, headers) if body is not None else None, 
                headers=headers
            )

            if response.status >= 400:
                raise ValueError(f"Request failed with status {response.status}")

            content = await self._parse_response_content(session, response)

            if not isinstance(content, HttpStreamResource):
                await session.close()

            return content
        except:
            await session.close()
            raise

    def _serialize_request_body(self, body: Any, headers: Optional[Dict[str, str]]) -> Any:
        content_type, _ = parse_options_header(get_header_value(headers, "Content-Type", ""))

        if content_type == "application/x-www-form-urlencoded":
            return urlencode(body)

        if isinstance(body, (str, bytes)):
            return body

        return json.dumps(body)
    
    async def _parse_response_content(self, session: aiohttp.ClientSession, response: aiohttp.ClientResponse) -> Any:
        content_type, _ = parse_options_header(response.headers.get("Content-Type", ""))

        if content_type == "application/json":
            return await response.json()

        if content_type.startswith("text/"):
            return await response.text()

        _, disposition = parse_options_header(response.headers.get("Content-Disposition", ""))
        filename = disposition.get("filename")

        return HttpStreamResource(session, response.content, content_type, filename)
