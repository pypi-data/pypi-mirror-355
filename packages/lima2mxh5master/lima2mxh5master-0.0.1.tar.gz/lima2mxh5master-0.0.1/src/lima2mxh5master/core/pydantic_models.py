import keyword
from typing import Any
from typing import Dict

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class InstanceMethodCall(BaseModel):
    """
    InstanceMethodCall is a Pydantic model that represents a call to an instance method.

    Attributes:
        class_name (str): The key identifying the target instance.
            This is aliased as "__class__".
        method_name (str): The name of the method to be called.
            This is aliased as "__method__". Method names starting with an underscore are not allowed.
        kwargs (Dict[str, Any]): A dictionary of keyword arguments to be passed to the method.
            This is aliased as "__kwargs__". Defaults to an empty dictionary.
        args (Dict[str, Any]): A dictionary of positional arguments to be passed to the method.
            This is aliased as "__args__". Defaults to an empty dictionary.

    Methods:
        method_name_valid(cls, v): A validator that ensures the method name does not start with an underscore.
            Raises:
                ValueError: If the method name starts with an underscore.
            Returns:
                str: The validated method name.
    """

    class_name: str = Field(alias="__class__")
    method_name: str = Field(alias="__method__")
    kwargs: Dict[str, Any] = Field(default_factory=dict, alias="__kwargs__")
    args: Dict[str, Any] = Field(default_factory=dict, alias="__args__")

    @field_validator("method_name")
    def method_name_valid(cls, v):
        if v.startswith("_"):
            raise ValueError("Method name cannot start with underscore")
        return v

    @field_validator("class_name")
    def validate_class_name(cls, v):
        if not v.isidentifier():
            raise ValueError("Class name must be a valid Python identifier.")
        if keyword.iskeyword(v):
            raise ValueError("Class name cannot be a Python keyword.")
        return v
