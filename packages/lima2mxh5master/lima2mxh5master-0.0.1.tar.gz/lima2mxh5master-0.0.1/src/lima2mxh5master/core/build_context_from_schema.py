import ast
import importlib
import sys
import textwrap
from typing import Any
from typing import Dict
from typing import Set
from typing import Union

from esrf_pathlib import Path


def get_all_imports(file_path: Union[str, Path]) -> Set[str]:
    """
    Extract all top-level imported module names from a Python file.

    Parameters
    ----------
    file_path : str or Path
        Path to the Python file to analyze.

    Returns
    -------
    Set[str]
        Set of imported module names.
    """
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except SyntaxError as e:
        print(f"Error: Syntax error in {file_path}: {e}")
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    return imports


def list_missing_imports(file_path: Union[str, Path]) -> Set[str]:
    """
    List unresolved top-level import dependencies in a Python file.

    Parameters
    ----------
    file_path : str or Path
        Path to the Python file to check.

    Returns
    -------
    Set[str]
        Set of module names that cannot be resolved.
    """
    module_imports = get_all_imports(file_path)
    missing_dependencies = set()

    for module_name in module_imports:
        if module_name in sys.modules:
            continue
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                missing_dependencies.add(module_name)
        except Exception:
            missing_dependencies.add(module_name)

    return missing_dependencies


def load_class_from_custom_folder(
    class_name: str, custom_folders_class: list[Path]
) -> Any:
    """
    Dynamically load a class from a set of folders containing Python files.

    Parameters
    ----------
    class_name : str
        Name of the class to load.
    custom_folders_class : list of Path
        List of folders to search for Python files.

    Returns
    -------
    Any
        Loaded class object.

    Raises
    ------
    ImportError
        If the class cannot be found or imported, or if imports in the module fail.
    """
    for class_path in custom_folders_class:
        for filename in class_path.iterdir():
            if filename.suffix == ".py" and filename.name[0] != "_":
                module_name = filename.stem
                spec = importlib.util.spec_from_file_location(module_name, filename)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    missing_import = list_missing_imports(filename)
                    message = textwrap.dedent(
                        f"""\
                        Failed to import module {module_name}: {e}
                        Detected missing imports: {missing_import}
                    """
                    )
                    raise ImportError(message)

                if hasattr(module, class_name):
                    return getattr(module, class_name)

    raise ImportError(
        f"Class '{class_name}' not found in any file in '{custom_folders_class}'"
    )


def collect_class_names(schema: Any, found: Set[str] = None) -> Set[str]:
    """
    Recursively collect all unique class names from a nested schema.

    Parameters
    ----------
    schema : Any
        The schema object (nested dicts/lists) to parse.
    found : set of str, optional
        Set used for accumulating results across recursive calls.

    Returns
    -------
    set of str
        Set of class names found in the schema.
    """
    if found is None:
        found = set()

    if isinstance(schema, dict):
        if "__class__" in schema:
            found.add(schema["__class__"])
        for v in schema.values():
            collect_class_names(v, found)
    elif isinstance(schema, list):
        for item in schema:
            collect_class_names(item, found)

    return found


def populate_registry(
    registry: Dict[str, Dict[str, Any]], **kwargs: Any
) -> Dict[str, Dict[str, Any]]:
    """
    Populate class registry with required parameters from kwargs.

    Parameters
    ----------
    registry : dict
        Dictionary mapping class names to parameter dictionaries.
    **kwargs : Any
        Parameters to inject into the registry.

    Returns
    -------
    dict
        Updated registry with injected values.

    Raises
    ------
    ValueError
        If required parameters are missing or if registry is improperly structured.
    """
    for class_name, par_dict in registry.items():
        if isinstance(par_dict, dict):
            for par_name, par_value in par_dict.items():
                if par_value == "__REQUIRED__":
                    if par_name in kwargs:
                        registry[class_name][par_name] = kwargs.get(par_name, None)
                    else:
                        raise ValueError(
                            f"""Missing required parameter '{par_name}' for class '{class_name}'
                            Please provide it in the kwargs or update the registry.
                            Ex: dumpdicttonx(dict_h5, path_h5_master_file, {par_name}=...)
                            """
                        )
        else:
            raise ValueError(
                f"Registry entry parameter '{par_name}' must be a dictionary."
            )

    return registry


def build_context_from_schema(
    schema: Dict[str, Any],
    registry: Dict[str, Dict[str, Any]],
    class_folder_paths: list[Union[Path, str]],
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Build a context dictionary by instantiating classes defined in a schema.

    Parameters
    ----------
    schema : dict
        The input schema containing class definitions under `__class__` keys.
    registry : dict
        Mapping from class names to constructor arguments.
    class_folder_paths : list of str or Path
        List of folders to search for class definition files.
    **kwargs : Any
        Additional parameters to fill in registry requirements.

    Returns
    -------
    dict
        Dictionary mapping class names to instantiated class objects.

    Raises
    ------
    ValueError
        If class registry entries are missing or malformed.
    ImportError
        If a required class cannot be found or loaded.
    """
    registry = populate_registry(registry, **kwargs)
    target_names = collect_class_names(schema)
    context = {}

    custom_folders_class = [Path(__file__).resolve().parents[1] / "custom"]
    for folder in class_folder_paths:
        if isinstance(folder, str):
            folder = Path(folder)
        if folder.is_dir():
            custom_folders_class.append(folder)

    for name in target_names:
        if name not in registry:
            raise ValueError(f"Missing class registry entry for: '{name}'")

        class_name = name
        init_args = registry[class_name]

        cls = load_class_from_custom_folder(
            class_name, custom_folders_class=custom_folders_class
        )
        context[name] = cls(**init_args)

    return context
