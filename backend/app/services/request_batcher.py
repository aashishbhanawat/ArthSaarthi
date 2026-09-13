import logging
from typing import Any, Callable, Dict, List, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BatchQuoteFetcher:
    """
    Utility for partitioning large asset lists into optimal sub-batches to prevent
    exceeding external API provider payload or URI length limits.
    """

    def __init__(self, max_batch_size: int = 50):
        self.max_batch_size = max_batch_size

    def partition(self, items: List[T]) -> List[List[T]]:
        """
        Splits a list of items into chunks of up to max_batch_size.
        """
        if not items:
            return []
        return [
            items[i : i + self.max_batch_size]
            for i in range(0, len(items), self.max_batch_size)
        ]

    def execute_batch_fetch(
        self,
        items: List[Dict[str, Any]],
        fetch_fn: Callable[[List[Dict[str, Any]]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Partition items into sub-batches, invoke fetch_fn for each sub-batch,
        and aggregate the results into a single dictionary.
        """
        if not items:
            return {}

        chunks = self.partition(items)
        aggregated_results: Dict[str, Any] = {}

        for index, chunk in enumerate(chunks):
            logger.debug(
                f"Executing batch fetch chunk {index + 1}/{len(chunks)} with {len(chunk)} items"
            )
            try:
                chunk_result = fetch_fn(chunk)
                if isinstance(chunk_result, dict):
                    aggregated_results.update(chunk_result)
            except Exception as e:
                logger.error(f"Error in batch fetch chunk {index + 1}: {e}")
                # Continue fetching remaining batches even if one batch fails

        return aggregated_results
