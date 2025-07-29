from typing import Type, Union, Literal, Optional, Dict, List, Tuple, Set, Annotated, Any
from pydantic import BaseModel, Field
from pydantic import model_validator
from .component import ComponentConfig

class JobConfig(BaseModel):
    component: Optional[Union[ str, ComponentConfig ]] = "__default__"
    action: Optional[str] = "__default__"
    input: Optional[Dict[str, Any]] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = Field(default_factory=dict)
    depends_on: Optional[List[str]] = Field(default_factory=list)

class WorkflowConfig(BaseModel):
    description: Optional[str] = None
    jobs: Optional[Dict[str, JobConfig]] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = Field(default_factory=dict)
    default: bool = False

    @model_validator(mode="before")
    def inflate_single_job(cls, values):
        if "jobs" not in values:
            job_keys = set(JobConfig.model_fields.keys())
            if any(k in values for k in job_keys):
                values["jobs"] = { "__default__": { k: values.pop(k) for k in job_keys if k in values } }
        return values
