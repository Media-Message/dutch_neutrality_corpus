#!/usr/bin/env python3
import argparse
import logging

from dutch_neutrality_corpus.pipeline import Pipeline, Stage
from dutch_neutrality_corpus.revision_retrieval import (
    retrieve_single_revision
)
from dutch_neutrality_corpus.utils import (
    LoadJSONStage,
    SaveIterableToJSONStage
)

logging.basicConfig(level='INFO')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extract revision IDs from wiki meta history dump.')
    parser.add_argument('--input-file',
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
    input_file = str(args.input_file)
    output_file = str(args.output_file)

    stages = [
        LoadJSONStage(
            filepath=input_file,
            select_fields=['revision_id'],
        ),
        Stage(func=retrieve_single_revision, filter_collection=True),
        SaveIterableToJSONStage(filepath=output_file)
    ]

    pipeline = Pipeline(stages=stages)
    results = pipeline.apply(collection=None)
