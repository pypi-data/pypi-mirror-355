from typing import List, Dict, Union, Optional, Any, Set

import datasets
import evaluate

_DESCRIPTION = """\
Precision at K (P@k) is an evaluation metric for ranked retrieval tasks.
It measures the proportion of relevant items found among the top k retrieved items.
P@k = (Number of relevant items in the top k retrieved items) / k.
This implementation allows for computing P@k for multiple k values and P@NR,
where NR is the number of relevant items for a query.
If predictions for a query are fewer than k, the precision is calculated with k as the denominator.
"""

_KWARGS_DESCRIPTION = """
Args:
    predictions (list of lists): A list where each inner list contains the IDs of retrieved items,
        sorted by relevance, for a single query.
    references (list of lists/sets): A list where each inner list/set contains the IDs of
        the true relevant items for the corresponding query.
    k_values (list of int, optional): A list of k values for which to compute P@k.
        Defaults to [10].
    compute_per_nr (bool, optional): If True, computes P@NR for each query, where NR is the
        number of relevant items for that query. The result will be under 'precision_at_NR'.
        Defaults to False.

Returns:
    (dict): A dictionary with keys like 'precision_at_K' for each k in k_values,
    and 'precision_at_NR' if compute_per_nr is True. Values are the mean P@k
    (or P@NR) scores averaged over all queries.
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


def precision_at_k(retrieved_items: List[Any], relevant_items: Union[List[Any], Set[Any]], k: int) -> float:
    """
    Calculates Precision at K (P@k).

    P@k = (Number of relevant items in the top k retrieved items) / k

    Args:
        retrieved_items: A list of item IDs retrieved by the system, in ranked order.
        relevant_items: A list or set of item IDs that are truly relevant for the query.
        k: The cut-off for the number of retrieved items to consider.

    Returns:
        The precision at k, a float between 0.0 and 1.0.

    Raises:
        ValueError: If k is not a positive integer.
    """
    if not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer.")
    if not isinstance(retrieved_items, list):
        raise TypeError("retrieved_items must be a list.")
    if not isinstance(relevant_items, (list, set)):
        raise TypeError("relevant_items must be a list or set.")

    # If no items were retrieved, precision is 0.
    if not retrieved_items:
        return 0.0

    # Ensure relevant_ids is a set for efficient lookup
    relevant_set = set(relevant_items)

    # Consider only the first k retrieved items
    # If fewer than k items were retrieved, all retrieved items are considered.
    # The denominator is still k.
    top_k_retrieved = retrieved_items[:k]

    num_relevant_in_top_k = 0
    for item_id in top_k_retrieved:
        if item_id in relevant_set:
            num_relevant_in_top_k += 1

    return num_relevant_in_top_k / k


@evaluate.utils.file_utils.add_start_docstrings(_DESCRIPTION, _KWARGS_DESCRIPTION)
class PrecisionAtK(evaluate.Metric):

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
            compute_per_NR: bool = False  # noqa
    ) -> Dict[str, float]:
        if not predictions or not references:
            raise ValueError("Empty predictions and references provided")

        if len(predictions) != len(references):
            raise ValueError(
                f"Mismatch in the number of predictions ({len(predictions)}) and references ({len(references)})"
            )

        if k_values is None:
            k_values = [10]

        if not predictions:  # No queries to evaluate
            results = {}
            for k_val in k_values:
                results[f"precision_at_{k_val}"] = 0.0
            if compute_per_NR:
                results["precision_at_NR"] = 0.0
            return results

        per_query_scores = {f"p_at_{k_val}": [] for k_val in k_values}
        if compute_per_NR:
            per_query_scores["p_at_NR"] = []

        for pred_items, ref_items in zip(predictions, references):
            relevant_set = set(ref_items)

            for k_val in k_values:
                # Use the standalone function (or reimplement its logic here)
                score = precision_at_k(pred_items, relevant_set, k_val)
                per_query_scores[f"p_at_{k_val}"].append(score)

            if compute_per_NR:
                NR = len(relevant_set)
                if NR > 0:  # P@NR is only meaningful if there are relevant items
                    score_nr = precision_at_k(pred_items, relevant_set, NR)
                    per_query_scores["p_at_NR"].append(score_nr)
                elif per_query_scores["p_at_NR"] is not None:  # only append if NR=0 means P@NR=0 if any items retrieved
                    # If NR=0, any retrieved item is non-relevant. P@0 is tricky.
                    # Typically, if NR=0, P@k is 0. P@NR (P@0) is ill-defined or 0.
                    # Let's say if NR=0, P@NR = 0 if items are retrieved, or 1 if no items retrieved (perfect null retrieval)
                    # For simplicity, if NR=0, score is 0.
                    per_query_scores["p_at_NR"].append(0.0)

        results = {}
        for k_val in k_values:
            key = f"p_at_{k_val}"
            mean_score = sum(per_query_scores[key]) / len(per_query_scores[key]) if per_query_scores[key] else 0.0
            results[f"precision_at_{k_val}"] = mean_score

        if compute_per_NR:
            key_nr = "p_at_NR"
            if per_query_scores[key_nr]:  # Only if there were queries with NR > 0 or NR=0 scores were added
                mean_score_nr = sum(per_query_scores[key_nr]) / len(per_query_scores[key_nr])
            else:  # e.g. all queries had NR=0, and we didn't add scores for them
                mean_score_nr = 0.0
            results["precision_at_NR"] = mean_score_nr

        return results
