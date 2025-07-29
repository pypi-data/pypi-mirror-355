from typing import Dict, Any, List

import datasets
import evaluate
import numpy as np

_DESCRIPTION = """\
Normalized Average Rank metric for Information Retrieval (IR) evaluation.
    
Unlike traditional IR metrics (P@K, R@K) that require preset cutoff points, this metric provides
a global view of ranking quality. It applies to various IR tasks including:
text retrieval, CBIR, question answering, recommendation systems, code retrieval,
and academic literature search.

Based on the paper "Performance Evaluation in Content-Based Image Retrieval: 
Overview and Proposals" by Müller et al. (2001), Section 5, but generalized
for the entire IR field.

Formula: R̄ank = (1/(N·NR)) * (∑(i=1 to NR) Ri - NR(NR-1)/2)

Where:
- N: collection size (total number of items in database)
- NR: number of relevant items for the query
- Ri: rank at which the i-th relevant item is retrieved

The measure is 0 for perfect performance and approaches 1 as performance worsens.
Provides cross-dataset comparability through dual normalization by collection size
and number of relevant items.
"""

_KWARGS_DESCRIPTION = """\
- predictions: List of ranked item IDs or indices for each query (documents, images, products, etc.)
- references: List of relevant item IDs or indices for each query  
- collection_size: Total number of items in the database/collection
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
class NormalizedAverageRank(evaluate.Metric):

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
            collection_size: int,
    ) -> Dict[str, Any]:

        if not predictions or not references:
            raise ValueError("Empty predictions and references provided")

        if len(predictions) != len(references):
            raise ValueError(
                f"Mismatch in the number of predictions ({len(predictions)}) and references ({len(references)})"
            )

        normalized_ranks = []

        for pres, refs in zip(predictions, references):
            if not refs:
                continue

            N = collection_size
            NR = len(refs)
            if N == 0 or NR == 0:
                continue

            relevant_set = set(str(item) for item in refs)
            relevant_ranks = []
            for rank, item_id in enumerate(pres, start=1):
                if str(item_id) in relevant_set:
                    relevant_ranks.append(rank)

                if len(relevant_ranks) == len(relevant_set):
                    break

            # Handle case where not all relevant items are found
            # Assign the worst possible rank (collection_size) to missing items
            while len(relevant_ranks) < len(relevant_set):
                relevant_ranks.append(collection_size)

            sum_ranks = sum(relevant_ranks)
            expected_sum = NR * (NR + 1) / 2

            normalized_rank = (1 / (N * NR)) * (sum_ranks - expected_sum)
            normalized_ranks.append(normalized_rank)

        if not normalized_ranks:
            return {"normalized_ranks": 0.0}
        return {
            "normalized_average_rank": np.mean(normalized_ranks),
            "normalized_ranks": normalized_ranks,
            "total_queries": len(normalized_ranks),
        }
