from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, AsyncIterator, Any
from mindor.dsl.schema.component import HttpClientComponentConfig
from mindor.dsl.schema.action import ActionConfig, HttpClientActionConfig, HttpClientCompletionConfig
from mindor.core.listener import HttpCallbackListener
from mindor.core.utils.http_headers import parse_options_header, get_header_value
from mindor.core.utils.resources import StreamResource
from .base import BaseComponent, ComponentType, ComponentEngineMap
from .context import ComponentContext

from urllib.parse import urlencode
import asyncio, aiohttp, json

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

class HttpClientAction:
    def __init__(self, base_url: Optional[str], config: HttpClientActionConfig):
        self.base_url: Optional[str] = base_url
        self.config: HttpClientActionConfig = config
        self.future: Optional[asyncio.Future] = None

    async def run(self, context: ComponentContext) -> Any:
        url     = self._resolve_request_url(context)
        method  = context.render_template(self.config.method)
        params  = context.render_template(self.config.params)
        body    = context.render_template(self.config.body)
        headers = context.render_template(self.config.headers)

        response = await self._request(url, method, params, body, headers)

        if response:
            context.register_source("response", response)

        if self.config.completion:
            result = await self._handle_completion(self.config.completion, context)

        return context.render_template(self.config.output) if self.config.output else (result or response)

    async def _request(self, url: str, method: str, params: Optional[Dict[str, Any]], body: Optional[Any], headers: Optional[Dict[str, str]]) -> Any:
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

            if isinstance(content, HttpStreamResource):
                pass
            else:
                await session.close()

            return content
        except:
            await session.close()
            raise

    def _resolve_request_url(self, context: ComponentContext) -> str:
        if self.base_url and self.config.path:
            return context.render_template(str(self.base_url)) + context.render_template(self.config.path)

        return context.render_template(str(self.config.endpoint))
    
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

    async def _handle_completion(self, completion: HttpClientCompletionConfig, context: ComponentContext) -> Any:
        if completion.type == "callback":
            future: asyncio.Future = asyncio.get_event_loop().create_future()
            HttpCallbackListener.register_pending_future(context.render_template(completion.wait_for), future)
            result = await future
            if result:
                context.register_source("result", result)
            return result

        if completion.type == "polling":
            return None

class HttpClientComponent(BaseComponent):
    def __init__(self, id: str, config: HttpClientComponentConfig, env: Dict[str, str], daemon: bool):
        super().__init__(id, config, env, daemon)

    async def _serve(self) -> None:
        pass

    async def _shutdown(self) -> None:
        pass

    async def _run(self, action: ActionConfig, context: ComponentContext) -> Any:
        return await HttpClientAction(self.config.base_url, action).run(context)

ComponentEngineMap[ComponentType.HTTP_CLIENT] = HttpClientComponent
