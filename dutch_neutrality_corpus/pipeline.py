
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
