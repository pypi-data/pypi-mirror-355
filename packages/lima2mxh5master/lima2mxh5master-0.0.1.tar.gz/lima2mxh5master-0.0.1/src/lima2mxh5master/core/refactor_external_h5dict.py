from typing import Any
from typing import Union

from lima2mxh5master.core.pydantic_models import InstanceMethodCall


def _resolve_path(parent_path, key) -> str:
    """
    Constructs a full hierarchical path by appending a key to a parent path.

    Args:
        parent_path (str): The base path to which the key will be appended.
                           If None or "/", the key will be treated as the root path.
        key (str): The key to append to the parent path.

    Returns:
        str: The resulting hierarchical path.
    """
    if not parent_path or parent_path == "/":
        return f"/{key}"
    return f"{parent_path}/{key}"


def execute_instance_method(data_item: dict, context: dict) -> Any:
    """
    Executes a method on a target instance retrieved from the provided context.

    This function validates the input data, retrieves the target instance from
    the context using the specified key, and invokes the specified method on
    the instance with the provided arguments and keyword arguments.

    Args:
        data_item (dict): A dictionary containing the details of the method call.
            Expected keys include:
            - 'target_instance_key': The key to locate the target instance in the
                context.
            - 'method_name': The name of the method to invoke on the target instance.
            - 'args': A list of positional arguments to pass to the method.
            - 'kwargs': A dictionary of keyword arguments to pass to the method.
        context (dict): A dictionary mapping instance keys to their corresponding
            objects.

    Returns:
        Any: The result of the method call on the target instance.
    """

    call_info = InstanceMethodCall.model_validate(data_item)
    class_name = call_info.class_name
    method_name = call_info.method_name
    args = call_info.args
    kwargs = call_info.kwargs

    target_instance = context.get(class_name)
    if target_instance is None:
        raise ValueError(f"Instance '{class_name}' not found in the provided context.")

    method_to_call = getattr(target_instance, method_name)

    if not callable(method_to_call):
        raise TypeError(
            f"Attribute '{method_name}' on instance '{class_name}' is not callable."
        )

    result = method_to_call(*args, **kwargs)
    return result


def refactor_external_calls(
    data_item: Union[dict, list], context: dict, current_hdf5_path: str = "/"
) -> Any:
    """
    Recursively processes a nested nx structure (dictionary or list) to handle
    external calls, such as executing instance methods or
    functions, and updates the structure accordingly.
    Example of extertnal call:
    {
        "__class__": "my_instance",
        "__method__": "my_method",
        "args": [1, 2],
        "kwargs": {"key": "value"}
    }

    Args:
        data_item (dict | list): The input data structure to process. It can be a
            dictionary or a list containing nested elements.
        context (dict): A dictionary providing the context required for executing
            instance methods or functions.
        current_hdf5_path (str, optional): The current HDF5 path being processed.
            Defaults to "/".

    Returns:
        dict | list | None: The processed data structure with external calls
        resolved. Returns `None` if the processed dictionary or list is empty.

    Behavior:
        - If `data_item` is a dictionary:
            - Checks for special keys like `__class__` and `__method__`
              to execute instance methods.
            - Recursively processes nested dictionaries and updates their HDF5 paths.
        - If `data_item` is a list:
            - Recursively processes each element in the list and updates their
              HDF5 paths.
        - If `data_item` is neither a dictionary nor a list, it is returned as-is.
    """
    if isinstance(data_item, dict):

        if "__class__" in data_item and "__method__" in data_item:
            return execute_instance_method(data_item, context)

        processed_dict = {}
        for key, value in data_item.items():
            if key.startswith("@"):
                processed_dict[key] = value
            else:
                child_hdf5_path = _resolve_path(current_hdf5_path, key)
                processed_value = refactor_external_calls(
                    value, context, child_hdf5_path
                )
                if processed_value is not None:
                    processed_dict[key] = processed_value
        return processed_dict if processed_dict else None

    elif isinstance(data_item, list):
        processed_list = [
            refactor_external_calls(elem, context, f"{current_hdf5_path}[{i}]")
            for i, elem in enumerate(data_item)
        ]
        return [item for item in processed_list if item is not None]
    else:
        return data_item
