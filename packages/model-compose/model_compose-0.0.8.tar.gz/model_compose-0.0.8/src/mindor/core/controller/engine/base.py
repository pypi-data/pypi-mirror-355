from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from dataclasses import dataclass

from mindor.dsl.schema.controller import ControllerConfig, ControllerType
from mindor.dsl.schema.component import ComponentConfig
from mindor.dsl.schema.listener import ListenerConfig
from mindor.dsl.schema.workflow import WorkflowConfig
from mindor.core.services import AsyncService
from mindor.core.component import BaseComponent, create_component
from mindor.core.listener import BaseListener, create_listener
from mindor.core.workflow import Workflow, WorkflowResolver, create_workflow
from mindor.core.utils.workqueue import WorkQueue
from mindor.core.utils.expiring import ExpiringDict

from threading import Lock
import asyncio, ulid

@dataclass
class TaskState:
    task_id: str
    status: Literal[ "pending", "processing", "completed", "failed" ]
    output: Optional[Any] = None
    error: Optional[Any] = None

class BaseController(AsyncService):
    def __init__(self, config: ControllerConfig, components: Dict[str, ComponentConfig], listeners: List[ListenerConfig], workflows: Dict[str, WorkflowConfig], env: Dict[str, str], daemon: bool):
        super().__init__(daemon)

        self.config: ControllerConfig = config
        self.components: Dict[str, ComponentConfig] = components
        self.listeners: List[ListenerConfig] = listeners
        self.workflows: Dict[str, WorkflowConfig] = workflows
        self.env: Dict[str, str] = env
        self.queue: Optional[WorkQueue] = None
        self.task_states: ExpiringDict[TaskState] = ExpiringDict()
        self.task_states_lock: Lock = Lock()
        
        if self.config.max_concurrent_count > 0:
            self.queue = WorkQueue(self.config.max_concurrent_count, self._run_workflow)

    async def run_workflow(self, workflow_id: Optional[str], input: Dict[str, Any], wait_for_completion: bool = True) -> TaskState:
        task_id = ulid.ulid()
        state = TaskState(task_id=task_id, status="pending")
        with self.task_states_lock:
            self.task_states.set(task_id, state)

        if wait_for_completion:
            if self.queue:
                state = await (await self.queue.schedule(task_id, workflow_id, input))
            else:
                state = await self._run_workflow(task_id, workflow_id, input)
        else:
            asyncio.create_task(self._run_workflow(task_id, workflow_id, input))

        return state

    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        with self.task_states_lock:
            return self.task_states.get(task_id)

    async def _start(self) -> None:
        if self.queue:
            await self.queue.start()

        if self.daemon:
            await self._start_components()
            await self._start_listeners()

        await super()._start()

    async def _stop(self) -> None:
        if self.queue:
            await self.queue.stop()

        if self.daemon:
            await self._stop_listeners()
            await self._stop_components()

        await super()._stop()

    async def _start_components(self) -> None:
        await asyncio.gather(*[ component.start() for component in self._create_components() ])

    async def _stop_components(self) -> None:
        await asyncio.gather(*[ component.stop() for component in self._create_components() ])

    async def _start_listeners(self) -> None:
        await asyncio.gather(*[ listener.start() for listener in self._create_listeners() ])

    async def _stop_listeners(self) -> None:
        await asyncio.gather(*[ listener.stop() for listener in self._create_listeners() ])

    async def _run_workflow(self, task_id: str, workflow_id: Optional[str], input: Dict[str, Any]) -> TaskState:
        state = TaskState(task_id=task_id, status="processing")
        with self.task_states_lock:
            self.task_states.set(task_id, state)
        
        try:
            workflow = create_workflow(*WorkflowResolver(self.workflows).resolve(workflow_id), self.components, self.env)
            output = await workflow.run(task_id, input)
            state = TaskState(task_id=task_id, status="completed", output=output)
        except Exception as e:
            state = TaskState(task_id=task_id, status="failed", error=str(e))

        with self.task_states_lock:
            self.task_states.set(task_id, state, 1 * 3600)

        return state

    def _create_components(self) -> List[BaseComponent]:
        return [ create_component(component_id, config, self.env, self.daemon) for component_id, config in self.components.items() ]
    
    def _create_listeners(self) -> List[BaseListener]:
        return [ create_listener(config, self.env, self.daemon) for config in self.listeners ]
    
    def _create_workflow(self, workflow_id: Optional[str]) -> Workflow:
        return create_workflow(*WorkflowResolver(self.workflows).resolve(workflow_id), self.components, self.env)

ControllerEngineMap: Dict[ControllerType, Type[BaseController]] = {}
