from typing import Optional, Union

import evaluate
from datasets import DownloadConfig, DownloadMode
from evaluate.config import EVALUATION_MODULE_TYPES
from evaluate.module import EvaluationModule
from packaging.version import Version

from .inspect import _MODULES_BASE_DIR, _NAMESPACE, _MODULE_TYPE_DIRS


def load(
        path: str,
        config_name: Optional[str] = None,
        module_type: Optional[str] = None,
        process_id: int = 0,
        num_process: int = 1,
        cache_dir: Optional[str] = None,
        experiment_id: Optional[str] = None,
        keep_in_memory: bool = False,
        download_config: Optional[DownloadConfig] = None,
        download_mode: Optional[DownloadMode] = None,
        revision: Optional[Union[str, Version]] = None,
        **init_kwargs,
) -> EvaluationModule:
    if path.startswith(_NAMESPACE):
        name = path[len(_NAMESPACE) + 1:]
        module_types = []
        if module_type:
            module_types.append(module_type)
        else:
            module_types.extend(EVALUATION_MODULE_TYPES)
        for module_type in module_types:
            if module_type in _MODULE_TYPE_DIRS:
                module_path = _MODULES_BASE_DIR / _MODULE_TYPE_DIRS[module_type] / name
                if module_path.exists():
                    path = str(module_path)
                    break
    return evaluate.load(
        path=str(path),
        config_name=config_name,
        module_type=module_type,
        process_id=process_id,
        num_process=num_process,
        cache_dir=cache_dir,
        experiment_id=experiment_id,
        keep_in_memory=keep_in_memory,
        download_config=download_config,
        download_mode=download_mode,
        revision=revision,
        **init_kwargs,
    )
