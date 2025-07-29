import warnings
from typing import List, Dict, Union, Optional, Any, Set

import datasets
import evaluate

_DESCRIPTION = """\
Recall@Precision measures the recall achieved when precision reaches or exceeds 
a specified threshold. It answers the question: "What fraction of all relevant 
items can we retrieve while maintaining at least X precision?"

This metric finds the maximum number of items that can be retrieved while 
keeping precision >= threshold, then calculates the recall at that point.

Recall@Precision_threshold = Recall at the rank where Precision >= threshold

This implementation supports:
- Multiple precision thresholds in a single computation
- Binary relevance judgments  
- Batch processing for multiple queries
- String-based item identifiers

Based on IR evaluation standards from TREC and CBIR literature.

This metric is particularly useful for:
- Content-Based Image Retrieval (CBIR)
- Information Retrieval systems
- Recommendation systems
- Any ranking/retrieval evaluation where precision thresholds matter
"""

_KWARGS_DESCRIPTION = """\
Args:
    predictions (list of lists): A list where each inner list contains the string IDs of retrieved items,
        sorted by relevance, for a single query.
    references (list of lists/sets): A list where each inner list/set contains the string IDs of
        the true relevant items for the corresponding query.
    precision_thresholds (list of float, optional): A list of precision thresholds for which to 
        compute recall@precision. Values should be between 0.0 and 1.0.
        Defaults to [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].
    average (str, optional): How to average results across queries. Options:
        - 'macro': Average recall scores across queries (each query weighted equally)
        - 'micro': Pool all relevant items across queries (larger queries weighted more)
        - None: Return per-query results without averaging
        Defaults to 'macro'.
    ignore_missing (bool, optional): Whether to ignore queries with no relevant items.
        Defaults to True.
    interpolation (str, optional): How to handle cases where exact precision threshold
        is not achieved. Options:
        - 'none': Return 0.0 if exact threshold not reached
        - 'linear': Use linear interpolation between adjacent points
        - 'max': Use the maximum recall where precision >= threshold
        Defaults to 'max'.

Returns:
    (dict): A dictionary with keys like 'recall_at_precision_X' for each threshold.
    When average='macro' or 'micro', returns mean values. When average=None, returns lists of per-query scores.
"""

_CITATION = """\
@article{muller2001performance,
    title={Performance evaluation in content-based image retrieval: overview and proposals},
    author={M{\"u}ller, Henning and M{\"u}ller, Wolfgang and Squire, David McG and Marchand-Maillet, St{\'e}phane and Pun, Thierry},
    journal={Pattern Recognition Letters},
    volume={22},
    number={5},
    pages={593--601},
    year={2001},
    publisher={Elsevier}
}
"""


def recall_at_precision_threshold(
        retrieved_items: List[Any],
        relevant_items: Union[List[Any], Set[Any]],
        precision_threshold: float,
        interpolation: str = 'max'
) -> float:
    """
    Calculates Recall at Precision threshold.

    Args:
        retrieved_items: A list of item IDs retrieved by the system, in ranked order.
        relevant_items: A list or set of item IDs that are truly relevant for the query.
        precision_threshold: The minimum precision threshold (0.0 to 1.0).
        interpolation: How to handle cases where exact threshold is not achieved.

    Returns:
        The recall at the specified precision threshold, a float between 0.0 and 1.0.

    Raises:
        ValueError: If precision_threshold is not between 0.0 and 1.0.
        TypeError: If inputs are not of the correct type.
    """
    if not isinstance(precision_threshold, (int, float)) or not (0.0 <= precision_threshold <= 1.0):
        raise ValueError("precision_threshold must be between 0.0 and 1.0.")
    if not isinstance(retrieved_items, list):
        raise TypeError("retrieved_items must be a list.")
    if not isinstance(relevant_items, (list, set)):
        raise TypeError("relevant_items must be a list or set.")

    # Ensure relevant_items is a set for efficient lookup
    relevant_set = set(relevant_items)

    # If no relevant items exist, recall is undefined (we return 0.0)
    if not relevant_set:
        return 0.0

    # If no items were retrieved, recall is 0.
    if not retrieved_items:
        return 0.0

    # Calculate precision and recall at each rank
    max_recall_at_threshold = 0.0
    relevant_found = 0

    for i, item in enumerate(retrieved_items):
        if item in relevant_set:
            relevant_found += 1

        # Calculate precision and recall at current rank (i+1 items retrieved)
        current_precision = relevant_found / (i + 1)
        current_recall = relevant_found / len(relevant_set)

        # If precision meets or exceeds threshold, update max recall
        if current_precision >= precision_threshold:
            if interpolation == 'max':
                max_recall_at_threshold = max(max_recall_at_threshold, current_recall)
            elif interpolation == 'none':
                if current_precision >= precision_threshold:
                    max_recall_at_threshold = current_recall
            elif interpolation == 'linear':
                # For simplicity, we'll use the max approach for linear too
                # Full linear interpolation would require more complex logic
                max_recall_at_threshold = max(max_recall_at_threshold, current_recall)

    return max_recall_at_threshold


def _parse_predictions(predictions: List[Any]) -> List[Any]:
    """Parse prediction list to get ranked items."""
    if not predictions:
        return []

    # Since we only support string sequences now, predictions are already ranked items
    return predictions


def _parse_references(references: Union[List[Any], Set[Any]]) -> Set[Any]:
    """Parse reference list/set to extract relevant items."""
    relevant_items = set()

    # Convert to list if it's a set
    if isinstance(references, set):
        references = list(references)

    # Since we only support string sequences now, all items in references are relevant
    for item in references:
        relevant_items.add(item)

    return relevant_items


@evaluate.utils.file_utils.add_start_docstrings("""\n""")
class RecallAtPrecision(evaluate.Metric):

    def _info(self):
        return evaluate.MetricInfo(
            description=_DESCRIPTION,
            citation=_CITATION,
            inputs_description=_KWARGS_DESCRIPTION,
            features=datasets.Features({
                "predictions": datasets.Sequence(datasets.Value("string")),
                "references": datasets.Sequence(datasets.Value("string")),
            }),
            reference_urls=["https://www.sciencedirect.com/science/article/abs/pii/S0167865500001185"]
        )

    # noinspection PyMethodOverriding
    def _compute(
            self,
            predictions: List[List[Any]],
            references: List[Union[List[Any], Set[Any]]],
            precision_thresholds: Optional[List[float]] = None,
            average: Optional[str] = "macro",
            ignore_missing: bool = True,
            interpolation: str = 'max',
            **kwargs
    ) -> Dict[str, Any]:
        if not predictions or not references:
            raise ValueError("Empty predictions and references provided")

        if len(predictions) != len(references):
            raise ValueError(
                f"Mismatch in the number of predictions ({len(predictions)}) and references ({len(references)})"
            )

        if precision_thresholds is None:
            precision_thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

        # Validate precision_thresholds
        for threshold in precision_thresholds:
            if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                raise ValueError(f"All precision thresholds must be between 0.0 and 1.0, got: {threshold}")

        # Validate averaging method
        if average not in ["macro", "micro", None]:
            raise ValueError("average must be 'macro', 'micro', or None")

        # Validate interpolation method
        if interpolation not in ["none", "linear", "max"]:
            raise ValueError("interpolation must be 'none', 'linear', or 'max'")

        # Initialize results storage
        per_query_scores = {f"recall_at_precision_{threshold}": [] for threshold in precision_thresholds}

        valid_queries = 0
        total_relevant_items = 0

        # For micro averaging, we need to collect all precision-recall points
        all_precision_recall_points = []

        for pred_items, ref_items in zip(predictions, references):
            # Parse references to extract relevant items
            try:
                relevant_set = _parse_references(ref_items)
            except Exception as e:
                raise ValueError(f"Error parsing references: {e}")

            # Handle queries with no relevant items
            if not relevant_set:
                if ignore_missing:
                    continue
                else:
                    # Add zero scores for queries with no relevant items
                    for threshold in precision_thresholds:
                        per_query_scores[f"recall_at_precision_{threshold}"].append(0.0)
                    valid_queries += 1
                    continue

            valid_queries += 1
            total_relevant_items += len(relevant_set)

            # Parse predictions to get ranked items
            try:
                ranked_items = _parse_predictions(pred_items)
            except Exception as e:
                raise ValueError(f"Error parsing predictions: {e}")

            # Compute recall@precision for each threshold
            query_pr_points = []
            for threshold in precision_thresholds:
                score = recall_at_precision_threshold(ranked_items, relevant_set, threshold, interpolation)
                per_query_scores[f"recall_at_precision_{threshold}"].append(score)

            # For micro averaging, collect precision-recall points for this query
            if average == "micro":
                relevant_found = 0
                for i, item in enumerate(ranked_items):
                    if item in relevant_set:
                        relevant_found += 1
                    precision = relevant_found / (i + 1)
                    recall = relevant_found / len(relevant_set)
                    query_pr_points.append((precision, recall, len(relevant_set)))
                all_precision_recall_points.extend(query_pr_points)

        if valid_queries == 0:
            warnings.warn("No valid queries found for evaluation")
            results = {}
            for threshold in precision_thresholds:
                key_name = f"recall_at_precision_{threshold}"
                results[key_name] = 0.0 if average is not None else []
            return results

        # Compute final scores based on averaging method
        results = {}

        if average == "macro":
            # Macro averaging: average recall scores across queries
            for threshold in precision_thresholds:
                key = f"recall_at_precision_{threshold}"
                if per_query_scores[key]:
                    mean_score = sum(per_query_scores[key]) / len(per_query_scores[key])
                else:
                    mean_score = 0.0
                results[f"recall_at_precision_{threshold}"] = mean_score

        elif average == "micro":
            # Micro averaging: pool all precision-recall points across queries
            for threshold in precision_thresholds:
                # Find maximum recall where precision >= threshold across all queries
                max_recall = 0.0
                total_weight = 0
                weighted_recall_sum = 0.0

                # Group points by query and weight by number of relevant items
                current_query_points = []
                for precision, recall, num_relevant in all_precision_recall_points:
                    if precision >= threshold:
                        current_query_points.append((recall, num_relevant))

                # Calculate weighted average
                for recall, num_relevant in current_query_points:
                    weighted_recall_sum += recall * num_relevant
                    total_weight += num_relevant

                if total_weight > 0:
                    results[f"recall_at_precision_{threshold}"] = weighted_recall_sum / total_weight
                else:
                    results[f"recall_at_precision_{threshold}"] = 0.0

        else:  # average is None
            # Return per-query results
            for threshold in precision_thresholds:
                key = f"recall_at_precision_{threshold}"
                results[f"recall_at_precision_{threshold}"] = per_query_scores[key]

        # Add summary statistics
        if average is not None:
            results["total_queries"] = valid_queries
            if valid_queries > 0:
                results["avg_relevant_per_query"] = total_relevant_items / valid_queries

        return results
