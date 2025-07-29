from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from typing_extensions import Self
from pydantic import BaseModel

from mindor.dsl.schema.controller import HttpServerControllerConfig
from mindor.dsl.schema.component import ComponentConfig
from mindor.dsl.schema.workflow import WorkflowConfig
from mindor.core.utils.resources import StreamResource 
from .base import BaseController, ControllerType, ControllerEngineMap, TaskState

from fastapi import FastAPI, APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
import asyncio, uvicorn

class WorkflowTaskRequestBody(BaseModel):
    workflow_id: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    wait_for_completion: bool = True
    output_only: bool = False

class TaskResult(BaseModel):
    task_id: str
    status: Literal[ "pending", "processing", "completed", "failed" ]
    output: Optional[Any] = None
    error: Optional[Any] = None

    @classmethod
    def from_instance(cls, instance: TaskState) -> Self:
        return cls(
            task_id=instance.task_id,
            status=instance.status,
            output=instance.output,
            error=instance.error
        )

class HttpServerController(BaseController):
    def __init__(self, config: HttpServerControllerConfig, components: Dict[str, ComponentConfig], workflows: Dict[str, WorkflowConfig], env: Dict[str, str], daemon: bool):
        super().__init__(config, components, workflows, env, daemon)
        
        self.server: Optional[uvicorn.Server] = None
        self.app: FastAPI = FastAPI()
        self.router: APIRouter = APIRouter()
        
        self._configure_routes()
        self.app.include_router(self.router, prefix=self.config.base_path)

    def _configure_routes(self):
        @self.router.post("/workflows")
        async def run_workflow(
            body: WorkflowTaskRequestBody = Body(...)
        ):
            state = await self.run_workflow(body.workflow_id, body.input, body.wait_for_completion)

            if body.output_only and body.wait_for_completion:
                if state.status == "failed":
                    raise HTTPException(status_code=500, detail=str(state.error))
                
                if isinstance(state.output, StreamResource):
                    return StreamingResponse(
                        state.output,
                        media_type=state.output.content_type,
                        headers = {
                            "Content-Disposition": f"attachment; filename={state.output.filename}"
                        } if state.output.filename else {},
                        #background=BackgroundTask(lambda: asyncio.create_task(state.output.close()))
                    )

                return state.output
            
            return JSONResponse(content=TaskResult.from_instance(state).model_dump(exclude_none=True))

        @self.router.get("/tasks/{task_id}")
        async def get_task_state(
            task_id: str,
            output_only: bool = False
        ):
            state = self.get_task_state(task_id)

            if not state:
                raise HTTPException(status_code=404, detail="Task not found.")
            
            if output_only:
                if state.status in [ "pending", "processing" ]:
                    raise HTTPException(status_code=202, detail="Task is still in progress.")
                
                if state.status == "failed":
                    raise HTTPException(status_code=500, detail=str(state.error))

                if isinstance(state.output, StreamResource):
                    return StreamingResponse(
                        state.output,
                        media_type=state.output.content_type,
                        headers = {
                            "Content-Disposition": f"attachment; filename={state.output.filename}"
                        } if state.output.filename else {},
                        # background=BackgroundTask(lambda: asyncio.create_task(state.output.close()))
                    )

                return state.output

            return JSONResponse(content=TaskResult.from_instance(state).model_dump(exclude_none=True))

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

ControllerEngineMap[ControllerType.HTTP_SERVER] = HttpServerController
