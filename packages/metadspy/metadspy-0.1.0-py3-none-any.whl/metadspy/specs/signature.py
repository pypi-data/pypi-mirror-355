from pydantic import BaseModel, model_validator
from typing import List, Optional, Literal

_PRIMITIVE_MAP = {
    "text": "str",
    "number": "int",
    "float": "float",
    "boolean": "bool",
    "list_text": "list[str]",
    "list_number": "list[int]",
    "list_float": "list[float]",
}

class IOField(BaseModel):
    name: str
    kind: Literal[
        "text", "number", "float", "boolean",
        "choices", "list_text", "list_number",
        "list_float"
    ] | None = None
    choices: Optional[List[str]] = None
    type: Optional[str] = None
    desc: Optional[str] = None

    @property
    def py_type(self) -> str:
        if self.type:
            return self.type
        
        if self.kind == "choices":
            if not self.choices:
                raise ValueError(f"{self.name}: 'choices' list required")
            items = ", ".join(f"'{c}'" for c in self.choices)
            return f"Literal[{items}]"
        
        return _PRIMITIVE_MAP.get(self.kind, "str")

class SignatureSpec(BaseModel):
    name: str
    docstring: Optional[str] = None
    inputs: List[IOField]
    outputs: List[IOField]
    instructions: Optional[str] = None

    @model_validator(mode="after")
    def check_inputs_outputs(self):
        if not self.inputs:
            raise ValueError("At least one input field is required")
        if not self.outputs:
            raise ValueError("At least one output field is required")
        return self