import json
import logging
import xml.etree.cElementTree as ET

logging.basicConfig(level='INFO')


class IOStage():

    def __init__(self, filepath):
        self.filepath = filepath

    def apply(self, collection):
        pass


class LoadXMLFileStage(IOStage):

    def __init__(self, filepath, n_revisions):
        super().__init__(filepath)
        self.n_revisions = n_revisions

    def truncate_generator(self, generator, first_n):
        return [generator.__next__() for _ in range(int(first_n))]

    # TODO: replace 'collection' with nuisance parameter...
    def apply(self, collection):

        context = ET.iterparse(
            self.filepath,
            events=("start", "end")
        )
        context = iter(context)

        # Ignore the root element
        event, root = context.__next__()

        if self.n_revisions:
            logging.info(
                f'Selecting first {self.n_revisions} from {self.filepath}'
            )

            context = self.truncate_generator(
                generator=context,
                first_n=self.n_revisions)

        return context


class SaveIterableToJSONStage(IOStage):

    def __init__(self, filepath):
        super().__init__(filepath)

    def log_statistics(self, collection):
        logging.info(f'Length of saved file: {len(collection)}')

    def apply(self, collection):
        self.log_statistics(collection)

        with open(self.filepath, 'w') as outfile:
            json.dump(collection, outfile)

        logging.info(f'Saved to {self.filepath}')
        return True


class LoadJSONStage(IOStage):

    def __init__(self,
                 filepath,
                 select_fields=None):
        super().__init__(filepath)
        self.select_fields = select_fields

    def filter_fields(self, collection, fields):

        if isinstance(fields, str):
            fields = [fields]

        new_collection = []
        for c in collection:
            new_collection.append(
                {k: v for k, v in c.items() if k in fields}
            )
        return new_collection

    def apply(self, collection):

        with open(self.filepath) as json_file:
            collection = json.load(json_file)

        if self.select_fields:
            return self.filter_fields(
                collection=collection,
                fields=self.select_fields
            )

        return collection
