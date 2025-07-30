from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from pydantic import BaseModel, Field
from pydantic import model_validator
from .common import CommonActionConfig

class CommonCompletionConfig(BaseModel):
    type: Literal[ "polling", "callback" ]

class PollingCompletionConfig(CommonCompletionConfig):
    type: Literal["polling"]
    endpoint: Optional[str] = None
    path: Optional[str] = None
    method: Literal[ "GET", "POST", "PUT", "DELETE", "PATCH" ] = "GET"
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)
    params: Optional[Dict[str, str]] = Field(default_factory=dict)
    status: Optional[str] = None
    success_when: Optional[str] = None
    fail_when: Optional[str] = None
    interval: Optional[str] = None
    timeout: Optional[str] = None

    @model_validator(mode="before")
    def validate_endpoint_or_path(cls, values: Dict[str, Any]):
        if bool(values.get("endpoint")) == bool(values.get("path")):
            raise ValueError("Either 'endpoint' or 'path' must be set, but not both.")
        return values

class CallbackCompletionConfig(CommonCompletionConfig):
    type: Literal["callback"]
    wait_for: str

HttpClientCompletionConfig = Annotated[ 
    Union[
        PollingCompletionConfig,
        CallbackCompletionConfig
    ],
    Field(discriminator="type")
]

class HttpClientActionConfig(CommonActionConfig):
    endpoint: Optional[str] = None
    path: Optional[str] = None
    method: Literal[ "GET", "POST", "PUT", "DELETE", "PATCH" ] = "POST"
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)
    params: Optional[Dict[str, str]] = Field(default_factory=dict)
    deferred: bool = False
    completion: Optional[HttpClientCompletionConfig] = None

    @model_validator(mode="before")
    def validate_endpoint_or_path(cls, values: Dict[str, Any]):
        if bool(values.get("endpoint")) == bool(values.get("path")):
            raise ValueError("Either 'endpoint' or 'path' must be set, but not both.")
        return values

    @model_validator(mode="after")
    def validate_completion_if_deferred(self):
        if self.deferred and self.completion is None:
            raise ValueError("If 'deferred' is true, 'completion' must be provided.")
        return self
