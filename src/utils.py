import logging
import xml.etree.cElementTree as ET

import pandas as pd

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


class SaveIterableToCSVStage(IOStage):

    def __init__(self, filepath, seperator='\t'):
        super().__init__(filepath)
        self.seperator = seperator

    def log_statistics(self, dataframe):
        logging.info(f'Length of saved file: {dataframe.shape[0]}')

    def apply(self, collection):

        dataframe = pd.DataFrame(collection)
        self.log_statistics(dataframe)

        dataframe.to_csv(self.filepath, sep=self.seperator)
        logging.info(f'Saved to {self.filepath}')

        return True


class LoadCSVStage(IOStage):

    def __init__(self,
                 filepath,
                 seperator='\t',
                 select_columns=None,
                 return_type=None):
        super().__init__(filepath)
        self.seperator = seperator
        self.select_columns = select_columns
        self.return_type = return_type

    def log_statistics(self, dataframe):
        logging.info(f'Loaded file from {self.filepath}')
        logging.info(f'Length of loaded file: {dataframe.shape[0]}')

    def apply(self, collection):
        dataframe = pd.read_csv(self.filepath, sep=self.seperator)
        self.log_statistics(dataframe)

        if isinstance(self.select_columns, str):
            self.select_columns = [self.select_columns]

        if self.select_columns:
            dataframe = dataframe[self.select_columns]

        if (self.select_columns and
                self.return_type == 'list_of_dicts'):
            return dataframe[self.select_columns].to_dict('records')

        if self.return_type == 'list':
            return dataframe.tolist()

        return dataframe
