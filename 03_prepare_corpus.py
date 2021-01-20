#!/usr/bin/env python3
import logging
import argparse

from src.pipeline import (
    Pipeline,
    Stage)
from src.text_processing import (
    apply_text_sanitation,
    apply_sentence_tokenization,
    apply_bert_tokenization
)
from src.revision_processing import (
    filter_on_first_tier_rules,
    apply_matching_rules,
    RowDeduplicationStage,
    FilterOnTextLengthStage
)
from src.utils import (
    LoadJSONStage,
    SaveIterableToJSONStage
)


logging.basicConfig(level='INFO')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extract revision IDs from wiki meta history dump.')
    parser.add_argument('--input-file',
                        type=str,
                        required=True,
                        help='filepath to revision text file')
    parser.add_argument('--output-file',
                        type=str,
                        required=False,
                        default='data/revisions_processed_text.json',
                        help='filepath for processed text')
    parser.add_argument('--model-cache',
                        type=str,
                        required=False,
                        default='bert-base-uncased-model',
                        help='filepath for cached BERT model')

    args = parser.parse_args()
    input_file = str(args.input_file)
    output_file = str(args.output_file)
    model_cache = str(args.model_cache)

    stages = [
        LoadJSONStage(
            filepath=input_file,
            select_fields=[
                'revision_id',
                'prior',
                'post',
                'prior_deleted',
                'post_added'
            ]
        ),
        # Hard filter on edits
        Stage(
            func=filter_on_first_tier_rules,
            func_kwargs={
                'filter_non_empty': True,
                'filter_deleted_and_added': True,
                'filter_single_edit': True
            },
            filter_collection=True
        ),
        # Text processing for prior text
        Pipeline(
            stages=[
                Stage(
                    func=apply_text_sanitation,
                    func_kwargs={
                        'apply_to_field': 'prior',
                        'new_field': 'prior_text'
                    },
                    accumulate=True
                ),
                Stage(
                    func=apply_sentence_tokenization,
                    func_kwargs={
                        'apply_to_field': 'prior_text',
                        'new_field': 'prior_sentences_raw'
                    },
                    accumulate=True
                ),
                Stage(
                    func=apply_bert_tokenization,
                    func_kwargs={
                        'apply_to_field': 'prior_sentences_raw',
                        'new_field': 'prior_sentences_tokens'
                    },
                    accumulate=True
                )
            ]),
        # Text processing for posterior text
        Pipeline(
            stages=[
                Stage(
                    func=apply_text_sanitation,
                    func_kwargs={
                        'apply_to_field': 'post',
                        'new_field': 'post_text'
                    },
                    accumulate=True
                ),
                Stage(
                    func=apply_sentence_tokenization,
                    func_kwargs={
                        'apply_to_field': 'post_text',
                        'new_field': 'post_sentences_raw'
                    },
                    accumulate=True
                ),
                Stage(
                    func=apply_bert_tokenization,
                    func_kwargs={
                        'apply_to_field': 'post_sentences_raw',
                        'new_field': 'post_sentences_tokens'
                    },
                    accumulate=True
                )
            ]),
        # Filtering rules
        Pipeline(
            stages=[
                Stage(func=apply_matching_rules, flatten=True),
                RowDeduplicationStage(
                    deduplication_fields=[
                        'revision_id',
                        'prior_sentence_raw',
                        'post_sentence_raw'
                    ]),
                FilterOnTextLengthStage(
                    field_a='prior_sentence_raw',
                    field_b='post_sentence_raw'
                )
            ]),
        SaveIterableToJSONStage(filepath=output_file)
    ]

    pipeline = Pipeline(stages=stages)
    results = pipeline.apply(collection=None)
