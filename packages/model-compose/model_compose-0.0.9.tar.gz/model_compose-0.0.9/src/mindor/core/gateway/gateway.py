from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from mindor.dsl.schema.gateway import GatewayConfig
from .engine import BaseGateway, GatewayEngineMap

def create_gateway(config: GatewayConfig, env: Dict[str, str], daemon: bool) -> BaseGateway:
    try:
        return GatewayEngineMap[config.type](config, env, daemon)
    except KeyError:
        raise ValueError(f"Unsupported gateway type: {config.type}")
