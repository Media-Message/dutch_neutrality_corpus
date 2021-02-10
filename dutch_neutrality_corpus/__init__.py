#!/usr/bin/env python3
import sys
import logging
import argparse

from dutch_neutrality_corpus.pipeline import (
    Pipeline,
    Stage)
from dutch_neutrality_corpus.comment_filtering import (
    apply_npov_identification)
from dutch_neutrality_corpus.diff_revisions import (
    apply_example_extraction
)
from dutch_neutrality_corpus.retrieve_revisions import (
    retrieve_single_revision
)
from dutch_neutrality_corpus.process_revisions import (
    filter_on_first_tier_rules,
    apply_example_generation,
    apply_matching_rules,
    RowDeduplicationStage,
    FilterOnTextLengthStage
)
from dutch_neutrality_corpus.utils import (
    LoadJSONFileStage,
    LoadCSVFileStage,
    LoadXMLFileStage,
    SaveIterableToJSONStage,
    SaveIterableToCSVStage
)
from dutch_neutrality_corpus.doccano import (
    apply_filter_for_doccano_format
)
from dutch_neutrality_corpus.category_filter import (
    apply_category_filter
)

logging.basicConfig(
    level='INFO',
    format='%(asctime)s %(message)s',
    filename='dwnc.log')


def main():

    parser = argparse.ArgumentParser(
        description='Process wiki meta history dump.')
    parser.add_argument('--pipeline-name',
                        type=str,
                        required=True,
                        help='pipeline: (identify, retrieve, prepare)')
    parser.add_argument('--input-file',
                        type=str,
                        required=True,
                        help='filepath to revision text file')
    parser.add_argument('--output-file',
                        type=str,
                        required=False,
                        default='data/revisions_processed_text.json',
                        help='filepath for processed text')
    parser.add_argument('--n_revisions',
                        default=None,
                        help='max number of revisions for "identify"')

    args = parser.parse_args()
    pipeline_name = str(args.pipeline_name)
    input_file = str(args.input_file)
    output_file = str(args.output_file)

    n_revisions = None
    if args.n_revisions:
        n_revisions = int(args.n_revisions)

    if pipeline_name == 'identify':
        stages = [
            LoadXMLFileStage(
                filepath=input_file,
                n_revisions=n_revisions
            ),
            Stage(func=apply_npov_identification, filter_collection=True),
            SaveIterableToJSONStage(filepath=output_file)
        ]
    elif pipeline_name == 'retrieve':
        stages = [
            LoadCSVFileStage(
                filepath=input_file,
                select_fields=['revision_id'],
                n_revisions=n_revisions
            ),
            # TODO: Filter collection=True
            Stage(func=retrieve_single_revision, filter_collection=True),
            SaveIterableToJSONStage(filepath=output_file)
        ]
    elif pipeline_name == 'diff':
        stages = [
            LoadJSONFileStage(
                filepath=input_file,
                n_revisions=n_revisions
            ),
            Stage(
                func=apply_category_filter,
                filter_collection=True),
            # Stage(
            #     func=apply_example_extraction,
            #     filter_collection=True),
            # SaveIterableToJSONStage(filepath=output_file)
        ]
    elif pipeline_name == 'prepare_doccano':
        stages = [
            LoadJSONFileStage(
                filepath=input_file,
                n_revisions=n_revisions
            ),
            Stage(func=apply_filter_for_doccano_format,
                  filter_collection=True),
            SaveIterableToJSONStage(
                filepath=output_file,
                write_as_array=False)
        ]

    # Run pipeline
    pipeline = Pipeline(stages=stages)
    _ = pipeline.apply(collection=None)


if __name__ == '__main__':
    main()
    sys.exit()
