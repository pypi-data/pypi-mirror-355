from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Callable, Iterator, Any

from mindor.dsl.schema.listener import HttpCallbackListenerConfig, HttpCallbackConfig
from mindor.core.utils.http_headers import parse_options_header, get_header_value
from mindor.core.utils.template import TemplateRenderer
from .base import BaseListener, ListenerType, ListenerEngineMap

from fastapi import FastAPI, APIRouter, Body, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from threading import Lock
import asyncio, uvicorn

_pending_futures: Dict[str, asyncio.Future] = {}
_pending_futures_lock: Lock = Lock()

class HttpCallbackContext:
    def __init__(self, body: Optional[Any], query: Optional[Dict[str, str]], bulk: bool, item: Optional[str]):
        self.body: Optional[Any] = body
        self.query: Optional[Dict[str, str]] = query
        self.bulk: bool = bulk
        self.item: Optional[str] = item
        self.renderer: TemplateRenderer = TemplateRenderer(self._resolve_source)

    def items(self) -> Iterator["HttpCallbackContext"]:
        for item in self._items():
            yield HttpCallbackContext(item, self.query, False, None)

    def render_template(self, template: str) -> Any:
        return self.renderer.render(template)

    def _items(self) -> List[Any]:
        item = self.renderer.render(self.item) if self.item else self.body

        if self.bulk:
            if not isinstance(item, list):
               raise ValueError("Expected a list because 'bulk' is true, but got a non-list.")
            return item

        return [ item ]

    def _resolve_source(self, key: str) -> Any:
        if key == "body" or key == "item":
            return self.body
        if key == "query":
            return self.query
        raise KeyError(f"Unknown source: {key}")

class HttpCallbackListener(BaseListener):
    def __init__(self, config: HttpCallbackListenerConfig, env: Dict[str, str], daemon: bool):
        super().__init__(config, env, daemon)
        
        self.server: Optional[uvicorn.Server] = None
        self.app: FastAPI = FastAPI()
        self.router: APIRouter = APIRouter()

        self._configure_routes()
        self.app.include_router(self.router, prefix=self.config.base_path)

    def _configure_routes(self):
        for callback in self.config.callbacks:
            self.router.add_api_route(
                path=callback.path,
                endpoint=self._make_callback_handler(callback),
                methods=[callback.method],
                name=f"callback_{callback.path.strip('/').replace('/', '_')}",
            )

    def _make_callback_handler(self, callback: HttpCallbackConfig) -> Callable:
        async def handler(request: Request) -> Response:
            body, query = await self._parse_request_content(request), request.query_params
            context = HttpCallbackContext(body, query, callback.bulk, callback.item)

            for item in context.items():
                callback_id = item.render_template(callback.identify_by)
                future: asyncio.Future = self._get_pending_future(callback_id)

                if future:
                    future.set_result(item.render_template(callback.result) if callback.result else item.body)
                    self._remove_pending_future(callback_id)

            return Response()

        return handler

    async def _parse_request_content(self, request: Request) -> Any:
        content_type, _ = parse_options_header(request.headers.get("Content-Type", ""))

        if content_type == "application/json":
            return await request.json()

        if content_type.startswith("text/"):
            return str(await request.body())

        return await request.body()

    async def _serve(self) -> None:
        self.server = uvicorn.Server(uvicorn.Config(
            self.app, 
            host=self.config.host, 
            port=self.config.port, 
            log_level="info"
        ))
        await self.server.serve()
 
    async def _shutdown(self) -> None:
        self.server.should_exit = True

    def _get_pending_future(self, id: str) -> Optional[asyncio.Future]:
        with _pending_futures_lock:
            return _pending_futures.get(id)

    def _remove_pending_future(self, id: str) -> None:
        with _pending_futures_lock:
            _pending_futures.pop(id, None)

    @classmethod
    def register_pending_future(cls, id: str, future: asyncio.Future) -> None:
        with _pending_futures_lock:
            _pending_futures[id] = future

ListenerEngineMap[ListenerType.HTTP_CALLBACK] = HttpCallbackListener
