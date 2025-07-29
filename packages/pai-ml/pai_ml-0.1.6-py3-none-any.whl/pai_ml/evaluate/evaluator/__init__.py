from evaluate.evaluator import Evaluator
from typing import Dict, List
from pai_ml.evaluate.evaluator.cbir import CBIREvaluator
from evaluate.evaluator import check_task as hf_check_task

try:
    from transformers.pipelines import SUPPORTED_TASKS as SUPPORTED_PIPELINE_TASKS
    from transformers.pipelines import TASK_ALIASES as _TASK_ALIASES
    from transformers.pipelines import check_task as check_pipeline_task

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

SUPPORTED_EVALUATOR_TASKS = {
    "cbir": {
        "implementation": CBIREvaluator,
        "default_metric_name": None,
    }
}

TASK_ALIASES = {
    **_TASK_ALIASES,
    "pai/cbir": "cbir",
}


def get_supported_tasks() -> List[str]:
    """
    Returns a list of supported task strings.
    """
    return list(SUPPORTED_EVALUATOR_TASKS.keys())


def check_task(task: str) -> Dict:
    """
    Checks an incoming task string, to validate it's correct and returns the default Evaluator class and default metric
    name. It first performs a check to validata that the string is a valid `Pipeline` task, then it checks if it's a
    valid `Evaluator` task. `Evaluator` tasks are a subset of `Pipeline` tasks.
    Args:
        task (`str`):
            The task defining which evaluator will be returned. Currently accepted tasks are:
            - `"cbir"`
    Returns:
        task_defaults: `dict`, contains the implementation class of a give Evaluator and the default metric name.
    """
    if task in TASK_ALIASES:
        task = TASK_ALIASES[task]
    if task in SUPPORTED_EVALUATOR_TASKS:
        return SUPPORTED_EVALUATOR_TASKS[task]
    targeted_task = hf_check_task(task)
    if targeted_task is not None:
        return targeted_task
    raise KeyError(f"Unknown task {task}, available tasks are: {get_supported_tasks()}.")


def evaluator(task: str = None) -> Evaluator:
    """
    Utility factory method to build an [`Evaluator`].
    Evaluators encapsulate a task and a default metric name. They leverage `pipeline` functionality from `transformers`
    to simplify the evaluation of multiple combinations of models, datasets and metrics for a given task.
    Args:
        task (`str`):
            The task defining which evaluator will be returned. Currently accepted tasks are:
            - `"cbir"`: will return a [`CBIREvaluator`].
    Returns:
        [`Evaluator`]: An evaluator suitable for the task.
    Examples:
    ```python
    >>> from pai_ml.evaluate import evaluator
    >>> # CBIR evaluator
    >>> evaluator("cbir")
    ```"""
    if not TRANSFORMERS_AVAILABLE:
        raise ImportError(
            "If you want to use the `Evaluator` you need `transformers`. Run `pip install evaluate[transformers]`."
        )
    targeted_task = check_task(task)
    evaluator_class = targeted_task["implementation"]
    default_metric_name = targeted_task["default_metric_name"]
    return evaluator_class(task=task, default_metric_name=default_metric_name)
