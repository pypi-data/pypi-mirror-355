import warnings
from typing import List, Dict, Union, Optional, Any, Set

import datasets
import evaluate

_DESCRIPTION = """\
Recall@K measures the fraction of relevant items that are successfully 
retrieved in the top-K results. It answers the question: "Of all the 
items that should have been retrieved, how many were actually found 
in the top-K results?"

Recall@K = (Number of relevant items in top-K) / (Total number of relevant items)

This implementation supports:
- Multiple K values in a single computation
- Binary relevance judgments  
- Batch processing for multiple queries
- String-based item identifiers

Based on IR evaluation standards from TREC and CBIR literature.

This metric is particularly useful for:
- Content-Based Image Retrieval (CBIR)
- Information Retrieval systems
- Recommendation systems
- Any ranking/retrieval evaluation
"""

_KWARGS_DESCRIPTION = """\
Args:
    predictions (list of lists): A list where each inner list contains the string IDs of retrieved items,
        sorted by relevance, for a single query.
    references (list of lists/sets): A list where each inner list/set contains the string IDs of
        the true relevant items for the corresponding query.
    k_values (list of int, optional): A list of k values for which to compute R@k.
        Defaults to [1, 5, 10, 20, 50].
    compute_per_NR (bool, optional): If True, computes R@NR for each query, where NR is the
        number of relevant items for that query. The result will be under 'recall_at_NR'.
        Defaults to False.
    average (str, optional): How to average results across queries. Options:
        - 'macro': Average recall scores across queries (each query weighted equally)
        - 'micro': Pool all relevant items across queries (larger queries weighted more)
        - None: Return per-query results without averaging
        Defaults to 'macro'.
    relevance_threshold (float, optional): This parameter is kept for compatibility but
        has no effect since only binary relevance is supported. Defaults to 1.0.
    ignore_missing (bool, optional): Whether to ignore queries with no relevant items.
        Defaults to True.

Returns:
    (dict): A dictionary with keys like 'recall_at_K' for each k in k_values.
    When average='macro' or 'micro', returns mean values. When average=None, returns lists of per-query scores.
    Also includes 'recall_at_NR' if compute_per_NR is True.
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


def recall_at_k(retrieved_items: List[Any], relevant_items: Union[List[Any], Set[Any]], k: int) -> float:
    """
    Calculates Recall at K (R@k).

    R@k = (Number of relevant items in the top k retrieved items) / (Total number of relevant items)

    Args:
        retrieved_items: A list of item IDs retrieved by the system, in ranked order.
        relevant_items: A list or set of item IDs that are truly relevant for the query.
        k: The cut-off for the number of retrieved items to consider.

    Returns:
        The recall at k, a float between 0.0 and 1.0.

    Raises:
        ValueError: If k is not a positive integer.
        TypeError: If inputs are not of the correct type.
    """
    if not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer.")
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

    # Consider only the first k retrieved items
    top_k_retrieved = retrieved_items[:k]

    # Count relevant items in top k
    num_relevant_in_top_k = 0
    for item_id in top_k_retrieved:
        if item_id in relevant_set:
            num_relevant_in_top_k += 1

    return num_relevant_in_top_k / len(relevant_set)


def _parse_predictions(predictions: List[Any]) -> List[Any]:
    """Parse prediction list to get ranked items."""
    if not predictions:
        return []

    # Since we only support string sequences now, predictions are already ranked items
    return predictions


def _parse_references(references: Union[List[Any], Set[Any]], threshold: float = 1.0) -> Set[Any]:
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
class RecallAtK(evaluate.Metric):

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
            k_values: Optional[List[int]] = None,
            compute_per_NR: bool = False,  # noqa
            average: Optional[str] = "macro",
            relevance_threshold: float = 1.0,
            ignore_missing: bool = True,
            **kwargs
    ) -> Dict[str, Any]:
        if not predictions or not references:
            raise ValueError("Empty predictions and references provided")

        if len(predictions) != len(references):
            raise ValueError(
                f"Mismatch in the number of predictions ({len(predictions)}) and references ({len(references)})"
            )

        if k_values is None:
            k_values = [1, 5, 10, 20, 50]

        # Validate k_values
        for k in k_values:
            if not isinstance(k, int) or k <= 0:
                raise ValueError(f"All k values must be positive integers, got: {k}")

        # Validate averaging method
        if average not in ["macro", "micro", None]:
            raise ValueError("average must be 'macro', 'micro', or None")

        # Initialize results storage
        per_query_scores = {f"recall_at_{k_val}": [] for k_val in k_values}
        if compute_per_NR:
            per_query_scores["recall_at_NR"] = []

        valid_queries = 0
        total_relevant_items = 0
        total_retrieved_relevant = {k: 0 for k in k_values}
        total_retrieved_relevant_NR = 0  # noqa

        for pred_items, ref_items in zip(predictions, references):
            # Parse references to extract relevant items
            try:
                relevant_set = _parse_references(ref_items, relevance_threshold)
            except Exception as e:
                raise ValueError(f"Error parsing references: {e}")

            # Handle queries with no relevant items
            if not relevant_set:
                if ignore_missing:
                    continue
                else:
                    # Add zero scores for queries with no relevant items
                    for k_val in k_values:
                        per_query_scores[f"recall_at_{k_val}"].append(0.0)
                    if compute_per_NR:
                        per_query_scores["recall_at_NR"].append(0.0)
                    valid_queries += 1
                    continue

            valid_queries += 1
            total_relevant_items += len(relevant_set)

            # Parse predictions to get ranked items
            try:
                ranked_items = _parse_predictions(pred_items)
            except Exception as e:
                raise ValueError(f"Error parsing predictions: {e}")

            # Compute recall@k for each k value
            for k_val in k_values:
                score = recall_at_k(ranked_items, relevant_set, k_val)
                per_query_scores[f"recall_at_{k_val}"].append(score)

                # For micro averaging - count retrieved relevant items
                retrieved_relevant = min(len([item for item in ranked_items[:k_val] if item in relevant_set]),
                                         len(relevant_set))
                total_retrieved_relevant[k_val] += retrieved_relevant

            # Compute R@NR if requested
            if compute_per_NR:
                NR = len(relevant_set)
                score_nr = recall_at_k(ranked_items, relevant_set, NR)
                per_query_scores["recall_at_NR"].append(score_nr)

                # For micro averaging
                retrieved_relevant_nr = min(len([item for item in ranked_items[:NR] if item in relevant_set]),
                                            len(relevant_set))
                total_retrieved_relevant_NR += retrieved_relevant_nr

        if valid_queries == 0:
            warnings.warn("No valid queries found for evaluation")
            results = {}
            for k_val in k_values:
                key_name = f"recall_at_{k_val}"
                results[key_name] = 0.0 if average is not None else []
            if compute_per_NR:
                results["recall_at_NR"] = 0.0 if average is not None else []
            return results

        # Compute final scores based on averaging method
        results = {}

        if average == "macro":
            # Macro averaging: average recall scores across queries
            for k_val in k_values:
                key = f"recall_at_{k_val}"
                if per_query_scores[key]:
                    mean_score = sum(per_query_scores[key]) / len(per_query_scores[key])
                else:
                    mean_score = 0.0
                results[f"recall_at_{k_val}"] = mean_score

            if compute_per_NR:
                key_nr = "recall_at_NR"
                if per_query_scores[key_nr]:
                    mean_score_nr = sum(per_query_scores[key_nr]) / len(per_query_scores[key_nr])
                else:
                    mean_score_nr = 0.0
                results["recall_at_NR"] = mean_score_nr

        elif average == "micro":
            # Micro averaging: pool all relevant items across queries
            for k_val in k_values:
                results[f"recall_at_{k_val}"] = \
                    total_retrieved_relevant[k_val] / total_relevant_items if total_relevant_items > 0 else 0.0

            if compute_per_NR:
                results["recall_at_NR"] = \
                    total_retrieved_relevant_NR / total_relevant_items if total_relevant_items > 0 else 0.0

        else:  # average is None
            # Return per-query results
            for k_val in k_values:
                key = f"recall_at_{k_val}"
                results[f"recall_at_{k_val}"] = per_query_scores[key]

            if compute_per_NR:
                results["recall_at_NR"] = per_query_scores["recall_at_NR"]

        # Add summary statistics
        if average is not None:
            results["total_queries"] = valid_queries
            if valid_queries > 0:
                results["avg_relevant_per_query"] = total_relevant_items / valid_queries

        return results
