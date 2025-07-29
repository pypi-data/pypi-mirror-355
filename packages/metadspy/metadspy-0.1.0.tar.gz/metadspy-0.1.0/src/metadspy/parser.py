from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Any, Dict
from ruamel.yaml import YAML
import json
from metadspy.specs import LLMSpec, SignatureSpec, ModuleSpec

class AssertionSpec(BaseModel):
    type: str
    args: List[str] = []

class FewShotSpec(BaseModel):
    strategy: Literal['random','embedding']
    k: int = 0

class OptimizerSpec(BaseModel):
    metric: str
    dataset_path: str
    few_shot: Optional[FewShotSpec] = None

class FullSpec(BaseModel):
    signature: SignatureSpec
    module: ModuleSpec
    llm: LLMSpec
    assertions: Optional[List[AssertionSpec]] = []
    optimizers: Optional[OptimizerSpec] = None

def load_spec(path: str) -> FullSpec:
    """
    Load and validate a YAML or JSON spec. Return a FullSpec object.
    """
    yaml_loader = YAML(typ="safe")
    
    if path.endswith((".yml", ".yaml")):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml_loader.load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    
    return FullSpec.model_validate(data)
