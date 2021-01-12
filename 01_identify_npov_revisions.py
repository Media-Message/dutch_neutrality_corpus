#!/usr/bin/env python3
import argparse
import logging

from src.comment_filtering import apply_npov_identification

from src.utils import (
    LoadXMLFileStage,
    SaveIterableToCSVStage)

from src.pipeline import Pipeline, Stage

logging.basicConfig(level='INFO')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extract revision IDs from wiki meta history dump.')
    parser.add_argument('--meta-history-file',
                        type=str,
                        # nargs=1,
                        required=True,
                        help='filepath to wikipedia meta history XML file')
    parser.add_argument('--output-file',
                        type=str,
                        required=False,
                        default='revisions.csv',
                        help='filepath for CSV with revision IDs and comments')
    parser.add_argument('--n_revisions',
                        default=None,
                        help='max number of revisions to process')

    args = parser.parse_args()
    meta_history_file = str(args.meta_history_file)
    output_file = str(args.output_file)
    n_revisions = int(args.n_revisions)

    stages = [
        LoadXMLFileStage(
            filepath=meta_history_file,
            n_revisions=n_revisions
        ),
        Stage(func=apply_npov_identification),
        SaveIterableToCSVStage(filepath=output_file)
    ]

    pipeline = Pipeline(stages=stages)
    results = pipeline.run(collection=None)
