#!/usr/bin/env python3

import multiprocessing


class Stage():
    """
    Parallelises function as part of Pipeline object
    """

    def __init__(self,
                 func,
                 n_workers=None,
                 filter_collection=True):
        self.func = func
        self.n_workers = n_workers
        self.filter_collection = filter_collection

    def apply(self, collection):
        # Distributes work over cores
        pool = multiprocessing.Pool(self.n_workers)
        results = pool.imap(self.func, collection)

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

    def run(self, collection):
        for stage in self.stages:
            collection = stage.apply(collection)
        return collection
