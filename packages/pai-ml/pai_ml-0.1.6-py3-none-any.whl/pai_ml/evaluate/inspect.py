import os
from pathlib import Path
from typing import List

from evaluate import list_evaluation_modules as hf_list_evaluation_modules
from evaluate.config import EVALUATION_MODULE_TYPES

_NAMESPACE = "pai"
_MODULES_BASE_DIR = Path(__file__).parent
_MODULE_TYPE_DIRS = {
    "metric": "metrics",
    "comparison": "comparisons",
    "measurement": "measurements"
}


def _list_evaluation_modules(
        module_type
) -> List[str]:
    modules_dir = _MODULE_TYPE_DIRS[module_type]
    modules_dir_path = _MODULES_BASE_DIR / modules_dir
    pai_modules = []
    if modules_dir_path.exists():
        for module_dir in modules_dir_path.iterdir():
            if not module_dir.is_dir():
                continue
            module_dir_path = str(module_dir)
            filename = list(filter(lambda x: x, module_dir_path.replace(os.sep, "/").split("/")))[-1]
            if not filename.endswith(".py"):
                filename = filename + ".py"
            combined_path = module_dir.joinpath(filename)
            if combined_path.exists():
                pai_modules.append(_NAMESPACE + "/" + module_dir.name)
    return pai_modules


def list_evaluation_modules(
        module_type=None,
        include_community=True,
        with_details=False,
) -> List[str]:
    hf_modules = hf_list_evaluation_modules(
        module_type=module_type,
        include_community=include_community,
        with_details=with_details,
    )
    if module_type is None:
        pai_modules = []
        for module_type in EVALUATION_MODULE_TYPES:
            pai_modules.extend(_list_evaluation_modules(module_type))
    else:
        if module_type not in EVALUATION_MODULE_TYPES:
            raise ValueError(f"Invalid module type '{module_type}'. Has to be one of {EVALUATION_MODULE_TYPES}.")
        pai_modules = _list_evaluation_modules(module_type)
    return hf_modules + pai_modules
