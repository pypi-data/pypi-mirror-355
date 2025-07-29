from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Callable, Any
from abc import ABC, abstractmethod

from mindor.dsl.schema.component import ComponentConfig, ComponentType
from mindor.dsl.schema.action import ActionConfig
from mindor.core.utils.workqueue import WorkQueue
from .context import ComponentContext

from threading import Thread
import asyncio

class ActionResolver:
    def __init__(self, actions: Dict[str, ActionConfig]):
        self.actions = actions

    def resolve(self, action_id: Optional[str]) -> Tuple[str, ActionConfig]:
        action_id = action_id or self._find_default_id(self.actions)

        if not action_id in self.actions:
            raise ValueError(f"Action not found: {action_id}")

        return action_id, self.actions[action_id]

    def _find_default_id(self, actions: Dict[str, ActionConfig]) -> str:
        default_ids = [ action_id for action_id, action in actions.items() if action.default ]

        if len(default_ids) > 1: 
            raise ValueError("Multiple actions have default: true")

        if not default_ids and "__default__" not in actions:
            raise ValueError("No default action defined.")

        return default_ids[0] if default_ids else "__default__"

class BaseComponent(ABC):
    def __init__(self, id: str, config: ComponentConfig, env: Dict[str, str], daemon: bool):
        self.id: str = id
        self.config: ComponentConfig = config
        self.env: Dict[str, str] = env
        self.daemon: bool = daemon

        self.queue: Optional[WorkQueue] = None
        self.thread: Optional[Thread] = None
        self.thread_loop: Optional[asyncio.AbstractEventLoop] = None
        self.daemon_task: Optional[asyncio.Task] = None
        self.started: bool = False

        if self.config.max_concurrent_count > 0:
            self.queue = WorkQueue(self.config.max_concurrent_count, self._run)

    async def start(self, background: bool = False) -> None:
        if background:
            def _start_in_thread():
                self.thread_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.thread_loop)
                self.thread_loop.run_until_complete(self._start())
    
            self.thread = Thread(target=_start_in_thread)
            self.thread.start()
        else:
            await self._start()

    async def stop(self) -> None:
        if self.thread:
            future = asyncio.run_coroutine_threadsafe(self._stop(), self.thread_loop)
            future.result()
            self.thread_loop.close()
            self.thread_loop = None
            self.thread.join()
            self.thread = None
        else:
            await self._stop()

    async def wait_until_stopped(self) -> None:
        if self.thread:
            self.thread.join()

        if self.daemon_task:
            await self.daemon_task

    async def run(self, action_id: Union[str, None], call_id: str, input: Dict[str, Any]) -> Dict[str, Any]:
        _, action = ActionResolver(self.config.actions).resolve(action_id)
        context = ComponentContext(call_id, input, self.env)

        if self.queue:
            return await (await self.queue.schedule(action, context))

        return await self._run(action, context)

    async def _start(self) -> None:
        if self.queue:
            await self.queue.start()

        self.started = True

        if self.daemon:
            if not self.thread:
                self.daemon_task = asyncio.create_task(self._serve())
            else:
                await self._serve()

    async def _stop(self) -> None:
        if self.queue:
            await self.queue.stop()

        if self.daemon:
            await self._shutdown()

        self.started = False

    @abstractmethod
    async def _serve(self) -> None:
        pass

    @abstractmethod
    async def _shutdown(self) -> None:
        pass

    @abstractmethod
    async def _run(self, action: ActionConfig, context: ComponentContext) -> Any:
        pass

ComponentEngineMap: Dict[ComponentType, Type[BaseComponent]] = {}
