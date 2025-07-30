from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from mindor.dsl.schema.gateway import GatewayConfig, GatewayType
from mindor.core.services import AsyncService

class BaseGateway(AsyncService):
    def __init__(self, config: GatewayConfig, env: Dict[str, str], daemon: bool):
        super().__init__(daemon)

        self.config: GatewayConfig = config
        self.env: Dict[str, str] = env

GatewayEngineMap: Dict[GatewayType, Type[BaseGateway]] = {}
