#!/usr/bin/env python3
import argparse
import logging

from src.pipeline import Pipeline, Stage
from src.revision_retrieval import (
    retrieve_single_revision
)
from src.utils import (
    LoadCSVStage,
    SaveIterableToCSVStage
)

logging.basicConfig(level='INFO')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extract revision IDs from wiki meta history dump.')
    parser.add_argument('--revision-file',
                        type=str,
                        # nargs=1,
                        required=True,
                        help='filepath to wikipedia revision CSV file')
    parser.add_argument('--output-file',
                        type=str,
                        required=False,
                        default='revision_texts.csv',
                        help='filepath for CSV with revision IDs and comments')
    args = parser.parse_args()
    revision_file = str(args.revision_file)
    output_file = str(args.output_file)

    stages = [
        LoadCSVStage(
            filepath=revision_file,
            select_columns='revision_id',
            return_type='list'
        ),
        Stage(func=retrieve_single_revision),
        SaveIterableToCSVStage(filepath=output_file)
    ]

    pipeline = Pipeline(stages=stages)
    results = pipeline.run(collection=None)
