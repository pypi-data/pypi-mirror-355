import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

from datasets import Dataset
from evaluate.evaluator.base import EVALUATOR_COMPUTE_RETURN_DOCSTRING, EVALUTOR_COMPUTE_START_DOCSTRING, Evaluator
from evaluate.module import EvaluationModule
from evaluate.utils.file_utils import add_end_docstrings, add_start_docstrings
from typing_extensions import Literal

if TYPE_CHECKING:
    pass

TASK_DOCUMENTATION = r"""
    Examples:

    ```python
    >>> from pai_ml.evaluate import load
    >>> from datasets import Dataset

    >>> # Load the CBIR evaluator
    >>> cbir_evaluator = load("pai/cbir")

    >>> # Prepare sample data
    >>> predictions = [
    ...     ["doc1", "doc2", "doc3", "doc4", "doc5"],  # Query 1 results
    ...     ["itemA", "itemB", "itemC", "itemD"]       # Query 2 results  
    ... ]
    >>> references = [
    ...     ["doc1", "doc3", "doc5"],                  # Query 1 relevant items
    ...     ["itemB", "itemD", "itemE"]                # Query 2 relevant items
    ... ]

    >>> # Evaluate with all metrics
    >>> results = cbir_evaluator.compute(
    ...     predictions=predictions,
    ...     references=references,
    ...     collection_size=100,
    ...     k_values=[1, 5, 10],
    ...     precision_thresholds=[0.5, 0.7, 0.9]
    ... )
    >>> print(f"Precision@1: {results["precision_at_1"]:.3f}")
    >>> print(f"Recall@5: {results["recall_at_5"]:.3f}")
    >>> print(f"First Relevant Rank: {results["mean_first_relevant_rank"]:.2f}")
    ```

    ```python
    >>> # Selective metric computation
    >>> results = cbir_evaluator.compute(
    ...     predictions=predictions,
    ...     references=references,
    ...     collection_size=100,
    ...     compute_ranking_metrics=True,
    ...     compute_precision_at_k=True,
    ...     compute_recall_at_k=False,
    ...     compute_recall_at_precision=False
    ... )
    ```

    ```python
    >>> # Different averaging strategies
    >>> macro_results = cbir_evaluator.compute(
    ...     predictions=predictions,
    ...     references=references,
    ...     collection_size=100,
    ...     average="macro"  # Each query weighted equally
    ... )
    >>> 
    >>> micro_results = cbir_evaluator.compute(
    ...     predictions=predictions,
    ...     references=references,
    ...     collection_size=100,
    ...     average="micro"  # Larger queries weighted more
    ... )
    ```
"""


class CBIREvaluator(Evaluator):
    """
    Content-Based Image Retrieval (CBIR) and Information Retrieval evaluator.

    This CBIR evaluator can be loaded from [`load`] using the task name `pai/cbir`.

    The evaluator computes comprehensive IR evaluation metrics including:
    - Ranking metrics: First Relevant Rank, Normalized Average Rank
    - Precision metrics: Precision@K for multiple K values
    - Recall metrics: Recall@K for multiple K values, Recall@NR
    - Precision-Recall metrics: Recall@Precision for multiple thresholds

    This implementation leverages existing optimized metric implementations and combines
    their results into a unified evaluation report.
    """

    def __init__(self, task="pai/cbir", default_metric_name=None):
        super().__init__(task, default_metric_name=default_metric_name)

    @staticmethod
    def predictions_processor(predictions, label_mapping=None):
        """
        Process predictions to ensure correct format.

        Args:
            predictions: List of lists containing ranked retrieval results
            label_mapping: Not used for CBIR evaluation

        Returns:
            Processed predictions in the expected format
        """
        # Ensure predictions are in the correct format
        if not isinstance(predictions, list):
            raise ValueError("Predictions must be a list of lists")

        processed_predictions = []
        for pred in predictions:
            if not isinstance(pred, list):
                raise ValueError("Each prediction must be a list of item IDs")
            # Convert all items to strings for consistency
            processed_predictions.append([str(item) for item in pred])

        return {"predictions": processed_predictions}

    @staticmethod
    def references_processor(references):
        """
        Process references to ensure correct format.

        Args:
            references: List of lists/sets containing relevant items

        Returns:
            Processed references in the expected format
        """
        processed_references = []
        for ref in references:
            if isinstance(ref, set):
                # Convert set to list
                processed_references.append([str(item) for item in ref])
            elif isinstance(ref, list):
                # Convert all items to strings
                processed_references.append([str(item) for item in ref])
            else:
                raise ValueError("Each reference must be a list or set of item IDs")

        return {"references": processed_references}

    @add_start_docstrings(EVALUTOR_COMPUTE_START_DOCSTRING)
    @add_end_docstrings(EVALUATOR_COMPUTE_RETURN_DOCSTRING, TASK_DOCUMENTATION)
    def compute(
            self,
            model_or_pipeline: Any = None,  # noqa
            data: Union[str, Dataset] = None,  # noqa
            subset: Optional[str] = None,  # noqa
            split: Optional[str] = None,  # noqa
            metric: Union[str, EvaluationModule] = None,  # noqa
            strategy: Literal["simple", "bootstrap"] = "simple",  # noqa
            confidence_level: float = 0.95,  # noqa
            n_resamples: int = 9999,  # noqa
            device: int = None,  # noqa
            random_state: Optional[int] = None,  # noqa
            # CBIR-specific parameters
            predictions: Optional[List[List[str]]] = None,
            references: Optional[List[Union[List[str], Set[str]]]] = None,
            collection_size: int = None,
            k_values: Optional[List[int]] = None,
            precision_thresholds: Optional[List[float]] = None,
            compute_precision_at_k: bool = True,
            compute_recall_at_k: bool = True,
            compute_recall_at_precision: bool = True,
            compute_ranking_metrics: bool = True,
            compute_per_NR: bool = True,  # noqa
            average: Optional[str] = "macro",
            ignore_missing: bool = True,
            interpolation: str = "max",
            **kwargs
    ) -> Dict[str, Any]:
        """
        Compute comprehensive CBIR/IR evaluation metrics.

        Args:
            predictions (List[List[str]], *optional*): 
                List of lists containing ranked retrieval results for each query.
                Each inner list should contain item IDs sorted by relevance.
            references (List[Union[List[str], Set[str]]], *optional*):
                List of lists/sets containing relevant items for each query.
            collection_size (int):
                Size of the collection used for evaluation.
            k_values (List[int], *optional*, defaults to [1, 5, 10, 20, 50]):
                K values for Precision@K and Recall@K computation.
            precision_thresholds (List[float], *optional*, defaults to [0.1, 0.2, ..., 0.9]):
                Precision thresholds for Recall@Precision computation.
            compute_precision_at_k (bool, *optional*, defaults to True):
                Whether to compute Precision@K metrics.
            compute_recall_at_k (bool, *optional*, defaults to True):
                Whether to compute Recall@K metrics.
            compute_recall_at_precision (bool, *optional*, defaults to True):
                Whether to compute Recall@Precision metrics.
            compute_ranking_metrics (bool, *optional*, defaults to True):
                Whether to compute ranking metrics (First Relevant Rank, Normalized Average Rank).
            compute_per_NR (bool, *optional*, defaults to True):
                Whether to compute Recall@NR.
            average (str, *optional*, defaults to "macro"):
                How to average results across queries. Options: "macro", "micro", None.
            ignore_missing (bool, *optional*, defaults to True):
                Whether to ignore queries with no relevant items.
            interpolation (str, *optional*, defaults to "max"):
                Interpolation method for Recall@Precision. Options: "none", "linear", "max".
        """

        # Handle direct predictions/references input (bypass dataset processing)
        if predictions is not None and references is not None:
            return self._compute_cbir_metrics(
                predictions=predictions,
                references=references,
                collection_size=collection_size,
                k_values=k_values,
                precision_thresholds=precision_thresholds,
                compute_precision_at_k=compute_precision_at_k,
                compute_recall_at_k=compute_recall_at_k,
                compute_recall_at_precision=compute_recall_at_precision,
                compute_ranking_metrics=compute_ranking_metrics,
                compute_per_NR=compute_per_NR,
                average=average,
                ignore_missing=ignore_missing,
                interpolation=interpolation,
                **kwargs
            )
        elif model_or_pipeline is not None and data is not None:
            raise NotImplementedError(
                "Dataset-based evaluation is not yet implemented. "
                "Please provide predictions and references directly."
            )
        elif predictions is not None or references is not None:
            if predictions is None:
                raise ValueError("Missing 'predictions' parameter...")
            else:
                raise ValueError("Missing 'references' parameter...")
        else:
            raise ValueError("Empty predictions and references provided")

    def _compute_cbir_metrics(
            self,
            predictions: List[List[str]],
            references: List[Union[List[str], Set[str]]],
            collection_size: int = None,
            k_values: Optional[List[int]] = None,
            precision_thresholds: Optional[List[float]] = None,
            compute_precision_at_k: bool = True,
            compute_recall_at_k: bool = True,
            compute_recall_at_precision: bool = True,
            compute_ranking_metrics: bool = True,
            compute_per_NR: bool = True,  # noqa
            average: Optional[str] = "macro",
            ignore_missing: bool = True,
            interpolation: str = "max",
            **kwargs
    ) -> Dict[str, Any]:
        """
        Core method to compute CBIR metrics using individual metric implementations.
        """

        # Input validation
        if not predictions or not references:
            raise ValueError("Empty predictions and references provided")

        if len(predictions) != len(references):
            raise ValueError(
                f"Mismatch in the number of predictions ({len(predictions)}) and references ({len(references)})"
            )

        # Set defaults
        if k_values is None:
            k_values = [1, 5, 10, 20, 50]
        if precision_thresholds is None:
            precision_thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

        # Validate parameters
        for k in k_values:
            if not isinstance(k, int) or k <= 0:
                raise ValueError(f"All k values must be positive integers, got: {k}")

        for threshold in precision_thresholds:
            if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                raise ValueError(f"All precision thresholds must be between 0.0 and 1.0, got: {threshold}")

        if average not in ["macro", "micro", None]:
            raise ValueError("average must be 'macro', 'micro', or None")

        if interpolation not in ["none", "linear", "max"]:
            raise ValueError("interpolation must be 'none', 'linear', or 'max'")

        # Process inputs
        processed_predictions = self.predictions_processor(predictions)["predictions"]
        processed_references = self.references_processor(references)["references"]

        # Initialize the comprehensive results dictionary
        results = {}

        # Load individual metrics as needed
        try:
            # Import evaluate library for loading metrics
            from pai_ml.evaluate import load

            # Initialize metric instances
            metrics = {}

            if compute_ranking_metrics:
                metrics["first_relevant_rank"] = load("pai/first_relevant_rank")
                metrics["normalized_average_rank"] = load("pai/normalized_average_rank")

            if compute_precision_at_k:
                metrics["precision_at_k"] = load("pai/precision_at_k")

            if compute_recall_at_k:
                metrics["recall_at_k"] = load("pai/recall_at_k")

            if compute_recall_at_precision:
                metrics["recall_at_precision"] = load("pai/recall_at_precision")
        except ImportError as e:
            raise ImportError(f"Failed to load required metrics: {e}")

        # Compute ranking metrics
        if compute_ranking_metrics:
            try:
                frr_results = metrics["first_relevant_rank"].compute(
                    predictions=processed_predictions,
                    references=processed_references,
                )
                results["mean_first_relevant_rank"] = frr_results["mean_first_relevant_rank"]

                nar_results = metrics["normalized_average_rank"].compute(
                    predictions=processed_predictions,
                    references=processed_references,
                    collection_size=collection_size
                )
                results["normalized_average_rank"] = nar_results["normalized_average_rank"]
            except Exception as e:
                warnings.warn(f"Failed to compute ranking metrics: {e}")

        # Compute Precision@K metrics
        if compute_precision_at_k:
            try:
                precision_results = metrics["precision_at_k"].compute(
                    predictions=processed_predictions,
                    references=processed_references,
                    k_values=k_values
                )

                # Extract precision@k results
                for k in k_values:
                    key = f"precision_at_{k}"
                    if key in precision_results:
                        results[key] = precision_results[key]
            except Exception as e:
                warnings.warn(f"Failed to compute Precision@K metrics: {e}")

        # Compute Recall@K metrics  
        if compute_recall_at_k:
            try:
                recall_results = metrics["recall_at_k"].compute(
                    predictions=processed_predictions,
                    references=processed_references,
                    k_values=k_values,
                    compute_per_NR=compute_per_NR,
                    average=average,
                    ignore_missing=ignore_missing
                )

                # Extract recall@k results
                for k in k_values:
                    key = f"recall_at_{k}"
                    if key in recall_results:
                        results[key] = recall_results[key]

                # Extract recall@NR if computed
                if compute_per_NR and "recall_at_NR" in recall_results:
                    results["recall_at_NR"] = recall_results["recall_at_NR"]
            except Exception as e:
                warnings.warn(f"Failed to compute Recall@K metrics: {e}")

        # Compute Recall@Precision metrics
        if compute_recall_at_precision:
            try:
                rp_results = metrics["recall_at_precision"].compute(
                    predictions=processed_predictions,
                    references=processed_references,
                    precision_thresholds=precision_thresholds,
                    average=average,
                    ignore_missing=ignore_missing,
                    interpolation=interpolation
                )

                # Extract recall@precision results
                for threshold in precision_thresholds:
                    key = f"recall_at_precision_{threshold}"
                    if key in rp_results:
                        results[key] = rp_results[key]
            except Exception as e:
                warnings.warn(f"Failed to compute Recall@Precision metrics: {e}")

        # Compute summary statistics
        results["summary"] = self._compute_summary_statistics(
            processed_predictions, processed_references, ignore_missing
        )

        # Organize results into categories for better readability
        organized_results = self._organize_results(
            results,
            k_values,
            precision_thresholds,
            compute_ranking_metrics,
            compute_precision_at_k,
            compute_recall_at_k,
            compute_recall_at_precision,
            compute_per_NR
        )

        return organized_results

    @staticmethod
    def _compute_summary_statistics(predictions, references, ignore_missing):
        """Compute summary statistics about the evaluation."""
        total_queries = len(predictions)
        queries_with_no_relevant = 0
        total_relevant_items = 0
        valid_queries = 0

        for ref_items in references:
            relevant_count = len(set(ref_items)) if ref_items else 0

            if relevant_count == 0:
                queries_with_no_relevant += 1
                if not ignore_missing:
                    valid_queries += 1
            else:
                total_relevant_items += relevant_count
                valid_queries += 1

        return {
            "total_queries": valid_queries,
            "original_total_queries": total_queries,
            "queries_with_no_relevant": queries_with_no_relevant,
            "avg_relevant_per_query": total_relevant_items / valid_queries if valid_queries > 0 else 0.0,
            "total_relevant_items": total_relevant_items,
            "ignore_missing_applied": ignore_missing
        }

    @staticmethod
    def _organize_results(
            results,
            k_values,
            precision_thresholds,
            compute_ranking_metrics,
            compute_precision_at_k,
            compute_recall_at_k,
            compute_recall_at_precision,
            compute_per_NR  # noqa
    ):
        """Organize results into logical categories."""
        organized = {}

        # Ranking metrics
        if compute_ranking_metrics:
            organized["ranking_metrics"] = {}
            if "mean_first_relevant_rank" in results:
                organized["ranking_metrics"]["mean_first_relevant_rank"] = results["mean_first_relevant_rank"]
            if "normalized_average_rank" in results:
                organized["ranking_metrics"]["normalized_average_rank"] = results["normalized_average_rank"]

        # Precision metrics
        if compute_precision_at_k:
            organized["precision_metrics"] = {}
            for k in k_values:
                key = f"precision_at_{k}"
                if key in results:
                    organized["precision_metrics"][key] = results[key]

        # Recall metrics
        if compute_recall_at_k:
            organized["recall_metrics"] = {}
            for k in k_values:
                key = f"recall_at_{k}"
                if key in results:
                    organized["recall_metrics"][key] = results[key]

            if compute_per_NR and "recall_at_NR" in results:
                organized["recall_metrics"]["recall_at_NR"] = results["recall_at_NR"]

        # Precision-Recall metrics
        if compute_recall_at_precision:
            organized["precision_recall_metrics"] = {}
            for threshold in precision_thresholds:
                key = f"recall_at_precision_{threshold}"
                if key in results:
                    organized["precision_recall_metrics"][key] = results[key]

        # Summary
        if "summary" in results:
            organized["summary"] = results["summary"]

        # Return both organized and flat structures
        flat_results = {}
        for category, metrics in organized.items():
            if category == "summary":
                flat_results[category] = metrics
            else:
                flat_results.update(metrics)

        return {**flat_results, "organized": organized}
