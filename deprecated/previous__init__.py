#!/usr/bin/env python3
import sys
import logging
import argparse

from dutch_neutrality_corpus.pipeline import (
    Pipeline,
    Stage)
from dutch_neutrality_corpus.comment_filtering import (
    apply_npov_identification)
from dutch_neutrality_corpus.process_text import (
    apply_text_sanitation,
    apply_sentence_tokenization,
    apply_bert_tokenization
)
from dutch_neutrality_corpus.diff import (
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
from dutch_neutrality_corpus.io import (
    LoadJSONFileStage,
    LoadCSVFileStage,
    LoadXMLFileStage,
    SaveIterableToJSONStage,
    SaveIterableToCSVStage
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
        # TODO: use CSV temporarily...
        stages = [
            LoadCSVFileStage(
                filepath=input_file,
                select_fields=['revision_id'],
                n_revisions=n_revisions
            ),
            Stage(func=retrieve_single_revision, filter_collection=True),
            SaveIterableToJSONStage(filepath=output_file)
        ]
    elif pipeline_name == 'diff':
        # TODO: Move diff into final pipeline later...
        # stages = [
        #     LoadJSONFileStage(
        #         filepath=input_file,
        #         n_revisions=n_revisions
        #     ),
        #     Stage(func=diff_single_revision, filter_collection=True),
        #     SaveIterableToJSONStage(filepath=output_file)
        # ]
        stages = [
            LoadJSONFileStage(
                filepath=input_file,
                n_revisions=n_revisions
            ),
            Stage(
                func=apply_example_extraction,
                filter_collection=True,
                n_workers=1),
            SaveIterableToJSONStage(filepath=output_file)
        ]
    # elif pipeline_name == 'prepare':
    #     stages = [
    #         LoadJSONFileStage(
    #             filepath=input_file,
    #             n_revisions=n_revisions,
    #             select_fields=[
    #                 'revision_id',
    #                 'prior',
    #                 'post',
    #                 'prior_deleted',
    #                 'post_added'
    #             ]
    #         ),
    #         # Hard filter on edits
    #         Stage(
    #             func=filter_on_first_tier_rules,
    #             func_kwargs={
    #                 'filter_non_empty': True,
    #                 'filter_deleted_and_added': True,
    #                 'filter_single_edit': False  # Ignore for now.
    #             },
    #             filter_collection=True
    #         ),
    #         # Text processing for prior text
    #         Pipeline(
    #             stages=[
    #                 Stage(
    #                     func=apply_text_sanitation,
    #                     func_kwargs={
    #                         'apply_to_field': 'prior',
    #                         'new_field': 'prior_text'
    #                     },
    #                     accumulate=True
    #                 ),
    #                 Stage(
    #                     func=apply_sentence_tokenization,
    #                     func_kwargs={
    #                         'apply_to_field': 'prior_text',
    #                         'new_field': 'prior_sentences_raw'
    #                     },
    #                     accumulate=True
    #                 ),
    #                 Stage(
    #                     func=apply_bert_tokenization,
    #                     func_kwargs={
    #                         'apply_to_field': 'prior_sentences_raw',
    #                         'new_field': 'prior_sentences_tokens'
    #                     },
    #                     accumulate=True
    #                 )
    #             ]),
    #         # Text processing for posterior text
    #         Pipeline(
    #             stages=[
    #                 Stage(
    #                     func=apply_text_sanitation,
    #                     func_kwargs={
    #                         'apply_to_field': 'post',
    #                         'new_field': 'post_text'
    #                     },
    #                     accumulate=True
    #                 ),
    #                 Stage(
    #                     func=apply_sentence_tokenization,
    #                     func_kwargs={
    #                         'apply_to_field': 'post_text',
    #                         'new_field': 'post_sentences_raw'
    #                     },
    #                     accumulate=True
    #                 ),
    #                 Stage(
    #                     func=apply_bert_tokenization,
    #                     func_kwargs={
    #                         'apply_to_field': 'post_sentences_raw',
    #                         'new_field': 'post_sentences_tokens'
    #                     },
    #                     accumulate=True
    #                 )
    #             ]),
    #         # Filtering rules
    #         Pipeline(
    #             stages=[
    #                 Stage(func=apply_example_generation, flatten=True),
    #                 # Stage(func=apply_matching_rules, flatten=True),
    #                 # RowDeduplicationStage(
    #                 #     deduplication_fields=[
    #                 #         'revision_id',
    #                 #         'prior_sentence_raw',
    #                 #         'post_sentence_raw'
    #                 #     ]),
    #                 # FilterOnTextLengthStage(
    #                 #     field_a='prior_sentence_raw',
    #                 #     field_b='post_sentence_raw'
    #                 # )
    #             ]),
    #         # SaveIterableToCSVStage(filepath=output_file)
    #     ]

    # Run pipeline
    pipeline = Pipeline(stages=stages)
    _ = pipeline.apply(collection=None)


if __name__ == '__main__':
    main()
    sys.exit()
