from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Callable, Iterator, Any
from mindor.dsl.schema.gateway import HttpTunnelGatewayConfig
from .base import BaseGateway, GatewayType, GatewayEngineMap

class HttpTunnelGateway(BaseGateway):
    def __init__(self, config: HttpTunnelGatewayConfig, env: Dict[str, str], daemon: bool):
        super().__init__(config, env, daemon)
        
GatewayEngineMap[GatewayType.HTTP_TUNNEL] = HttpTunnelGateway
