from abc import ABC, abstractmethod
import time

class BatchStrategy(ABC):
    @abstractmethod
    def process(self, items: list, processor):
        pass

class FixedSizeBatchStrategy(BatchStrategy):
    def __init__(self, batch_size: int, delay_between_batches: float = 0):
        self.batch_size = batch_size
        self.delay = delay_between_batches

    def process(self, items: list, processor):
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            results.append(processor(batch))
            if self.delay > 0 and i + self.batch_size < len(items):
                time.sleep(self.delay)
        return results

class AdaptiveBatchStrategy(BatchStrategy):
    def __init__(self, initial_batch_size: int, min_batch_size: int, max_batch_size: int, delay_between_batches: float = 0):
        self.current_batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.delay = delay_between_batches

    def process(self, items: list, processor):
        results = []
        i = 0
        while i < len(items):
            batch_size = self.current_batch_size
            batch = items[i:i + batch_size]
            try:
                results.append(processor(batch))
                # On success, increase batch size
                self.current_batch_size = min(self.max_batch_size, int(batch_size * 1.5))
            except Exception as e:
                # On failure, decrease batch size
                self.current_batch_size = max(self.min_batch_size, int(batch_size * 0.5))
                # Optionally re-raise or handle error
                raise e

            i += len(batch)
            if self.delay > 0 and i < len(items):
                time.sleep(self.delay)
        return results
