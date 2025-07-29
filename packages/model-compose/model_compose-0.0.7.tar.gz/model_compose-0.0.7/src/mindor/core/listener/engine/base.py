from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mindor.dsl.schema.listener import ListenerConfig, ListenerType
from mindor.core.listener import BaseListener, create_listener

class BaseListener(ABC):
    def __init__(self, config: ListenerConfig, env: Dict[str, str]):
        self.config: ListenerConfig = config
        self.env: Dict[str, str] = env

ListenerEngineMap: Dict[ListenerType, Type[BaseListener]] = {}
