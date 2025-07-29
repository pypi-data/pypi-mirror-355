from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from mindor.dsl.schema.listener import ListenerConfig
from .engine import BaseListener, ListenerEngineMap

def create_listener(config: ControllerConfig, env: Dict[str, str]) -> BaseListener:
    try:
        return ListenerEngineMap[config.type](config, env)
    except KeyError:
        raise ValueError(f"Unsupported listener type: {config.type}")
