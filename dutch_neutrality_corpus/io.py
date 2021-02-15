import os
import json
import csv
import logging
import types
import multiprocessing
from functools import partial
import xml.etree.cElementTree as ET

logging.basicConfig(
    level='INFO',
    format='%(asctime)s %(message)s',
    filename='dwnc.log')


class IOStage():

    def __init__(self, filepath):
        self.filepath = filepath

    def apply(self, collection):
        pass


class LoadCSVFileStage(IOStage):

    def __init__(self,
                 filepath,
                 n_revisions=None,
                 select_fields=None,
                 n_workers=None):
        super().__init__(filepath)
        self.n_revisions = n_revisions
        self.select_fields = select_fields
        self.n_workers = n_workers

    def filter_dict(self, item_dict, fields):
        return {k: v for k, v in item_dict.items() if k in fields}

    def filter_fields(self, collection, fields):

        if isinstance(fields, str):
            fields = [fields]

        pool = multiprocessing.Pool(self.n_workers)

        kwargs = {'fields': fields}
        filter_func = partial(
            self.filter_dict,
            **kwargs)

        return pool.imap(filter_func, collection)

    def apply(self, collection):
        logging.info(f'Loading {self.filepath}...')

        with open(self.filepath, "r") as f:
            reader = csv.DictReader(f)
            collection = list(reader)

        if self.n_revisions:
            logging.info(
                f'Selecting first {self.n_revisions} from {self.filepath}'
            )
            collection = collection[:self.n_revisions]

        if self.select_fields:
            logging.info('Filtering fields...')
            collection = self.filter_fields(
                collection=collection,
                fields=self.select_fields
            )

        logging.info(f'Completed loading {self.filepath}')

        return collection


class LoadXMLFileStage(IOStage):

    def __init__(self, filepath, n_revisions):
        super().__init__(filepath)
        self.n_revisions = n_revisions

    def truncate_generator(self, generator, first_n):
        return (generator.__next__() for _ in range(int(first_n)))

    # TODO: replace 'collection' with nuisance parameter...
    def apply(self, collection):
        logging.info(f'Loading {self.filepath}...')

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

        logging.info(f'Completed loading {self.filepath}')

        return context


class SaveIterableToJSONStage(IOStage):

    def __init__(self, filepath, from_dict=False, write_as_array=True):
        super().__init__(filepath)
        self.from_dict = from_dict
        self.write_as_array = write_as_array

    def log_statistics(self, collection):
        logging.info(f'Length of saved file: {len(collection)}')

    def write_file(self, collection, filepath, write_as_array):
        self.log_statistics(collection)

        if write_as_array:
            with open(filepath, 'w') as outfile:
                json.dump(collection, outfile)
        else:
            with open(filepath, 'w') as outfile:
                for row in collection:
                    json.dump(row, outfile)
                    outfile.write('\n')

        logging.info(f'Save complete to {filepath}')

    def apply(self, collection):
        logging.info(f'Saving {self.filepath}...')

        # Dict of filenames and collections
        if self.from_dict and isinstance(collection, dict):

            for filename, data in collection.items():
                full_file_path = os.path.join(self.filepath, filename)
                self.write_file(
                    collection=data,
                    filepath=full_file_path,
                    write_as_array=self.write_as_array)
        else:
            self.write_file(
                collection=self.collection,
                filepath=self.filepath,
                write_as_array=self.write_as_array)

        return True


class SaveIterableToCSVStage(IOStage):

    def __init__(self, filepath):
        super().__init__(filepath)

    def log_statistics(self, collection):
        logging.info(f'Length of saved file: {len(collection)}')

    def apply(self, collection):
        self.log_statistics(collection)

        logging.info(f'Saving {self.filepath}...')

        # TODO: make robust later...
        fields = collection[0].keys()
        with open(self.filepath, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fields)
            dict_writer.writeheader()
            dict_writer.writerows(collection)

        logging.info(f'Save complete to {self.filepath}')
        return True


class LoadJSONFileStage(IOStage):

    def __init__(self,
                 filepath,
                 n_revisions=None,
                 select_fields=None,
                 n_workers=None):
        super().__init__(filepath)
        self.n_revisions = n_revisions
        self.select_fields = select_fields
        self.n_workers = n_workers

    def filter_dict(self, item_dict, fields):
        return {k: v for k, v in item_dict.items() if k in fields}

    def filter_fields(self, collection, fields):

        if isinstance(fields, str):
            fields = [fields]

        pool = multiprocessing.Pool(self.n_workers)

        kwargs = {'fields': fields}
        filter_func = partial(
            self.filter_dict,
            **kwargs)

        return pool.imap(filter_func, collection)

    def apply(self, collection):

        logging.info(f'Loading {self.filepath}...')

        with open(self.filepath) as json_file:
            collection = json.load(json_file)

        logging.info(f'Completed loading {self.filepath}')

        if self.select_fields:
            logging.info('Filtering fields...')
            collection = self.filter_fields(
                collection=collection,
                fields=self.select_fields
            )

        if self.n_revisions:
            logging.info(
                f'Selecting first {self.n_revisions} from {self.filepath}'
            )
            collection = list(collection)[:self.n_revisions]

        return collection
