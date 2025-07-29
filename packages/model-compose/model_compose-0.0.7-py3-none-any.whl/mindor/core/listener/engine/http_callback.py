from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from typing_extensions import Self
from pydantic import BaseModel

from mindor.dsl.schema.listener import HttpCallbackListenerConfig
from .base import BaseListener, ListenerType, ListenerEngineMap

from fastapi import FastAPI, APIRouter, Body, HTTPException
import uvicorn

class HttpCallbackListener(BaseListener):
    def __init__(self, config: HttpCallbackListenerConfig, env: Dict[str, str]):
        super().__init__(config, env)
        
        self.server: Optional[uvicorn.Server] = None
        self.app: FastAPI = FastAPI()
        self.router: APIRouter = APIRouter()

        self._configure_routes()
        self.app.include_router(self.router, prefix=self.config.base_path)

    def _configure_routes(self):
        pass

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

ListenerEngineMap[ListenerType.HTTP_CALLBACK] = HttpCallbackListener
