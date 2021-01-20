#!/usr/bin/env python3

import multiprocessing
from functools import partial


class Stage():
    """
    Parallelises function as part of Pipeline object
    """

    def __init__(self,
                 func,
                 n_workers=None,
                 filter_collection=False,
                 func_kwargs={},
                 accumulate=False,
                 flatten=False):
        self.func = func
        self.n_workers = n_workers
        self.filter_collection = filter_collection
        self.func_kwargs = func_kwargs
        self.accumulate = accumulate
        self.flatten = flatten

    def update_collection(self, collection, results):
        """ Merge within stage """
        if not isinstance(results, list):
            results = list(results)
        return ({**c, **r} for c, r in zip(collection, results))

    def flatten_results(self, results):
        """ Merge within stage """
        return (row for rows in results for row in rows)

    def apply(self, collection):
        # Distributes work over cores
        pool = multiprocessing.Pool(self.n_workers)

        if self.func_kwargs:
            self.func = partial(
                self.func,
                **self.func_kwargs)

        results = pool.imap(self.func, collection)

        # Update collection with new results
        if self.accumulate:
            results = self.update_collection(collection, results)

        if self.flatten:
            results = self.flatten_results(results)

        # Remove empty elements
        if self.filter_collection:
            results = filter(None, results)

        return list(results)


class Pipeline():
    """
    Sequentially iterates over stages
    """

    def __init__(self, stages):
        self.stages = stages

    def apply(self, collection):
        for stage in self.stages:
            collection = stage.apply(collection)
        return collection
