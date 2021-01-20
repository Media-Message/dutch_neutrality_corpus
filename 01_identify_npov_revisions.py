#!/usr/bin/env python3
import argparse
import logging

from src.comment_filtering import apply_npov_identification

from src.utils import (
    LoadXMLFileStage,
    SaveIterableToJSONStage)

from src.pipeline import Pipeline, Stage

logging.basicConfig(level='INFO')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extract revision IDs from wiki meta history dump.')
    parser.add_argument('--input-file',
                        type=str,
                        required=True,
                        help='filepath to wikipedia meta history XML file')
    parser.add_argument('--output-file',
                        type=str,
                        required=False,
                        default='revisions.json',
                        help='filepath for CSV with revision IDs and comments')
    parser.add_argument('--n_revisions',
                        default=None,
                        help='max number of revisions to process')

    args = parser.parse_args()
    input_file = str(args.input_file)
    output_file = str(args.output_file)
    n_revisions = int(args.n_revisions)

    stages = [
        LoadXMLFileStage(
            filepath=input_file,
            n_revisions=n_revisions
        ),
        Stage(func=apply_npov_identification, filter_collection=True),
        SaveIterableToJSONStage(filepath=output_file)
    ]

    pipeline = Pipeline(stages=stages)
    results = pipeline.apply(collection=None)
