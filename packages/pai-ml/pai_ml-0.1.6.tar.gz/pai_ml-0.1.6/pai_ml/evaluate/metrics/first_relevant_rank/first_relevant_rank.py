from typing import List, Dict, Any, Optional

import datasets
import evaluate
import numpy as np

_DESCRIPTION = """\
First Relevant Rank (Rank1) metric measures the rank position where the first relevant item is retrieved.
This is a crucial metric in information retrieval and content-based image retrieval (CBIR) systems.

The metric returns the rank (1-indexed) of the highest-ranked relevant item. Lower values indicate better performance.
If no relevant items are found, it returns the max-rank value (default: 1000).

Based on the TREC evaluation methodology as described in:
"Performance Evaluation in Content-Based Image Retrieval: Overview and Proposals"
"""

_KWARGS_DESCRIPTION = """\
Args:
    predictions: List[List[str]] - A list of ranked retrieval results for each query.
                Each inner list contains the retrieved items in order of decreasing relevance.
    references: List[List[str]] - A list of relevant items for each query.
               Each inner list contains all items that are considered relevant for that query.
    max_rank: int - Maximum rank to consider. Items not found within this rank are assigned
             this value (default: 1000, following common CBIR practices).
             
             IMPORTANT: max_rank vs top_k distinction:
             - top_k: System physical limit (how many results the system actually returns)
             - max_rank: Evaluation focus (which rank positions we care about for evaluation)
             - Best practice: max_rank ≤ top_k to avoid evaluating non-existent positions
             
             Selection strategies for max_rank:
             - Strict evaluation (max_rank=5-10): Only care about top results
             - Standard web search (max_rank=10-20): Users typically check first page
             - Image browsing (max_rank=20-50): Users may scroll through more results  
             - Academic search (max_rank=50-200): Researchers examine more thoroughly
             - Comprehensive evaluation (max_rank=1000): Traditional IR standard
             
             Usage scenarios:
             - User experience studies: Set based on actual user behavior analysis
             - System comparison: Use same max_rank across all systems being compared
             - Real-time systems: Lower max_rank (5-20) emphasizes quick results
             - Offline analysis: Higher max_rank (100-1000) for thorough evaluation
             
    normalize: bool - Whether to normalize ranks by collection size (default: False).
    return_details: bool - Whether to return detailed per-query information (default: True).
    collection_size: Optional[int] - Size of the collection (for normalization).
    success_at_k: List[int] - List of k values for computing success@k metrics 
                 (default: [1, 5, 10, 20, 50]). These represent cutoff ranks for 
                 measuring retrieval success.

Returns:
    dict: Contains the following metrics:
        - first_relevant_ranks: List of first relevant rank for each query
        - mean_first_relevant_rank: Mean rank1 score across all queries  
        - median_first_relevant_rank: Median rank1 score
        - std_first_relevant_rank: Standard deviation of rank1 scores
        - success_rate: Proportion of queries with at least one relevant item found
        - success_at_k: Success rates at different cutoff ranks
        - total_queries: Total number of queries evaluated
        - successful_queries: Number of queries with at least one relevant item found

Examples:
    >>> # Basic usage with single query
    >>> metric = load_cbir_rank1_metric()
    >>> predictions = [["item_3", "item_1", "item_5", "item_2", "item_4"]]
    >>> references = [["item_1", "item_2"]]  # relevant items for query
    >>> results = metric.compute(predictions=predictions, references=references)
    >>> print(results['first_relevant_ranks'])
    [2]
    >>> print(results['mean_first_relevant_rank'])
    2.0

    >>> # Multiple queries evaluation
    >>> predictions = [
    ...     ["doc_a", "doc_b", "doc_c", "doc_d"],     # Query 1 results
    ...     ["img_x", "img_y", "img_z"],              # Query 2 results  
    ...     ["paper_1", "paper_2", "paper_3"]        # Query 3 results
    ... ]
    >>> references = [
    ...     ["doc_b", "doc_d"],    # Query 1 relevant items
    ...     ["img_z"],             # Query 2 relevant items
    ...     ["paper_unknown"]      # Query 3 relevant items (not found)
    ... ]
    >>> results = metric.compute(predictions=predictions, references=references)
    >>> print(results['first_relevant_ranks'])
    [2, 3, 1000]
    >>> print(results['success_rate'])
    0.6666666666666666

    >>> # Custom max_rank for mobile search scenario
    >>> predictions = [["result1", "result2", "result3", "result4", "result5"]]
    >>> references = [["result4"]]  # relevant item at position 4
    >>> results = metric.compute(predictions=predictions, references=references, max_rank=3)
    >>> print(results['first_relevant_ranks'])
    [3]  # Assigned max_rank because actual rank (4) > max_rank (3)

    >>> # Custom success_at_k for classification evaluation
    >>> predictions = [
    ...     ["cat", "dog", "bird"],           # Image 1 predictions
    ...     ["car", "truck", "bicycle"]       # Image 2 predictions  
    ... ]
    >>> references = [
    ...     ["cat"],        # Image 1 true label (rank 1)
    ...     ["bicycle"]     # Image 2 true label (rank 3)
    ... ]
    >>> results = metric.compute(
    ...     predictions=predictions, 
    ...     references=references,
    ...     success_at_k=[1, 2, 3]
    ... )
    >>> print(results['success_at_k'])
    {1: 0.5, 2: 0.5, 3: 1.0}

    >>> # Normalized ranks for cross-dataset comparison
    >>> predictions = [["item_a", "item_b", "item_c", "item_d", "item_e"]]
    >>> references = [["item_c"]]  # relevant at rank 3
    >>> results = metric.compute(
    ...     predictions=predictions, 
    ...     references=references,
    ...     normalize=True,
    ...     collection_size=100
    ... )
    >>> print(results['first_relevant_ranks'])
    [0.03]  # 3/100 = 0.03

    >>> # Image retrieval evaluation
    >>> search_results = [
    ...     ["beach1.jpg", "sunset2.jpg", "ocean3.jpg", "wave4.jpg"],
    ...     ["dog1.jpg", "cat2.jpg", "puppy3.jpg"]
    ... ]
    >>> relevant_images = [
    ...     ["ocean3.jpg", "wave4.jpg"],   # Beach query relevance
    ...     ["dog1.jpg", "puppy3.jpg"]     # Animal query relevance  
    ... ]
    >>> results = metric.compute(predictions=search_results, references=relevant_images)
    >>> print(f"Mean first relevant rank: {results['mean_first_relevant_rank']:.1f}")
    Mean first relevant rank: 1.5
    >>> print(f"Success@3: {results['success_at_k'][3]:.1f}")
    Success@3: 1.0

    >>> # Document retrieval with no relevant found
    >>> predictions = [["doc1", "doc2", "doc3"]]
    >>> references = [["doc_not_in_results"]]
    >>> results = metric.compute(predictions=predictions, references=references, max_rank=50)
    >>> print(results['first_relevant_ranks'])
    [50]  # Assigned max_rank penalty
    >>> print(results['success_rate'])
    0.0

    >>> # Empty predictions handling
    >>> predictions = [[]]  # System returned no results
    >>> references = [["item1"]]
    >>> results = metric.compute(predictions=predictions, references=references)
    >>> print(results['first_relevant_ranks'])
    [1000]  # Default max_rank assigned for empty predictions
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


@evaluate.utils.file_utils.add_start_docstrings(_DESCRIPTION, _KWARGS_DESCRIPTION)
class FirstRelevantRank(evaluate.Metric):

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
            predictions: List[List[str]],
            references: List[List[str]],
            max_rank: int = 1000,
            normalize: bool = False,
            return_details: bool = True,
            collection_size: Optional[int] = None,
            success_at_k: List[int] = None
    ) -> Dict[str, Any]:
        if not predictions or not references:
            raise ValueError("Empty predictions and references provided")

        if len(predictions) != len(references):
            raise ValueError(
                f"Mismatch in the number of predictions ({len(predictions)}) and references ({len(references)})"
            )

        if success_at_k is None:
            success_at_k = [1, 5, 10, 20, 50]

        actual_max_length = max(len(pred) for pred in predictions if pred) if any(predictions) else 0
        if 0 < actual_max_length < max_rank:
            import warnings
            warnings.warn(
                f"max_rank ({max_rank}) > maximum prediction length ({actual_max_length}). "
                f"Consider setting max_rank ≤ {actual_max_length} to avoid evaluating non-existent ranks. "
                f"This suggests your retrieval system's top_k={actual_max_length}."
            )

        if normalize and collection_size is None:
            collection_size = max(len(pred) for pred in predictions if pred)
            if collection_size == 0:
                collection_size = max_rank

        first_relevant_ranks = []
        query_details = [] if return_details else None
        # Initialize success@k counters using provided or default k values
        success_at_k_counts = {k: 0 for k in success_at_k}

        for query_idx, (pred_items, ref_items) in enumerate(zip(predictions, references)):
            query_detail: Dict[str, Any] = {
                "query_id": query_idx,
                "total_predictions": len(pred_items),
                "total_references": len(ref_items),
                "first_relevant_item": None,
                "first_relevant_rank": None,
                "status": None
            } if return_details else None

            # Handle empty cases
            if not pred_items or not ref_items:
                first_relevant_ranks.append(max_rank)
                if return_details:
                    query_detail["first_relevant_rank"] = max_rank
                    query_detail["status"] = "empty_input"
                    query_details.append(query_detail)
                continue

            ref_set = set(ref_items)
            first_relevant_rank = None
            first_relevant_item = None

            for rank, pred_item in enumerate(pred_items, 1):  # rank starts from 1 (standard practice)
                if pred_item in ref_set:
                    first_relevant_rank = rank
                    first_relevant_item = pred_item
                    break

            if first_relevant_rank is None:
                rank = max_rank
                status = "no_relevant_found"
            elif first_relevant_rank > max_rank:
                rank = max_rank
                status = "no_relevant_found"
            else:
                rank = first_relevant_rank
                status = "success"
                for k in success_at_k_counts:
                    if first_relevant_rank <= k:
                        success_at_k_counts[k] += 1

            if normalize and collection_size:
                if rank < max_rank:
                    rank = rank / collection_size  # e.g., rank 5 of 100 → 0.05
                else:
                    rank = 1.0  # Max normalized score for failures

            first_relevant_ranks.append(rank)

            if return_details:
                query_detail.update({
                    "first_relevant_item": first_relevant_item,
                    "first_relevant_rank": first_relevant_rank or max_rank,
                    "normalized_rank": rank if normalize else None,
                    "status": status
                })
                query_details.append(query_detail)

        valid_scores = [score for score in first_relevant_ranks if score < max_rank]

        total_queries = len(predictions)
        successful_queries = len(valid_scores)  # Queries that found ≥1 relevant item
        success_rate = successful_queries / total_queries if total_queries > 0 else 0.0
        success_at_k_results = {
            k: count / total_queries if total_queries > 0 else 0.0
            for k, count in success_at_k_counts.items()
        }

        if valid_scores:
            mean_first_relevant_rank = float(np.mean(valid_scores))
            median_first_relevant_rank = float(np.median(valid_scores))
            std_first_relevant_rank = float(np.std(valid_scores))
        else:
            mean_first_relevant_rank = None
            median_first_relevant_rank = None
            std_first_relevant_rank = None

        results = {
            "first_relevant_ranks": first_relevant_ranks,
            "mean_first_relevant_rank": mean_first_relevant_rank,
            "median_first_relevant_rank": median_first_relevant_rank,
            "std_first_relevant_rank": std_first_relevant_rank,
            "success_rate": success_rate,
            "success_at_k": success_at_k_results,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
        }

        if return_details:
            results["query_details"] = query_details

        return results
