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
    parser.add_argument('--revisions-text-file',
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
    revisions_text_file = str(args.revisions_text_file)
    output_file = str(args.output_file)
    model_cache = str(args.model_cache)

    stages = [
        LoadJSONStage(
            filepath=revisions_text_file,
            select_fields=[
                'revision_id',
                'prior',
                'post',
                'prior_deleted',
                'post_added'
            ]
        ),
        # TODO: Add first tier of filter for revisions
        # Pipeline(
        #     stages=[
        #         Stage(
        #             func=apply_text_sanitation,
        #             func_kwargs={
        #                 'apply_to_field': 'prior',
        #                 'new_field': 'prior_text'
        #             },
        #             accumulate=True
        #         ),
        #         Stage(
        #             func=apply_text_sanitation,
        #             func_kwargs={
        #                 'apply_to_field': 'prior',
        #                 'new_field': 'prior_text'
        #             },
        #             accumulate=True
        #         )
        #     ]),
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

    # TODO: ignore changes to nouns?
    # print([d for d in list(results) if d['is_word_edit']])

    # TODO: add writing to seperate files
    # print('WRITING...')
    # # write unbiased
    # f_unbiased = open(output_prefix + '.unbiased', 'w')
    # f_biased = open(output_prefix + '.biased', 'w')
    # f_word = open(output_prefix + '.wordbiased', 'w')

    # for ex in out:
    #     if ex['is_word_edit'] is None:
    #         f_unbiased.write(ex['out_row'] + '\n')
    #         continue

    #     # ratio skip - greater than 95th percentile
    #     r = ex['length_ratio']
    #     if (r < mu - 2.0 * sd) or (r > mu + 2.0 * sd):
    #         # CTR_LENGTH_RATIO += 1
    #         continue

    #     if ex['is_word_edit']:
    #         f_word.write(ex['out_row'] + '\n')

    #     f_biased.write(ex['out_row'] + '\n')

    # f_unbiased.close()
    # f_biased.close()
    # f_word.close()

    # print('ctrs:')

    # TODO: add logging of corpus statistics
    # print('CTR_EMPTY_REV', CTR_EMPTY_REV)
    # print('CTR_MULTIPLE_EDITS', CTR_MULTIPLE_EDITS)
    # print('CTR_FAILED_CLEANING', CTR_FAILED_CLEANING)
    # print('CTR_LOW_BLEU', CTR_LOW_BLEU)
    # print('CTR_LOW_LEVEN', CTR_LOW_LEVEN)
    # print('CTR_TOO_MANY_1_TOKS', CTR_TOO_MANY_1_TOKS)
    # print('CTR_SPELLING', CTR_SPELLING)
    # print('CTR_FALSE_POSITIVE', CTR_FALSE_POSITIVE)
    # print('CTR_LENGTH_RATIO', CTR_LENGTH_RATIO)
    # print('CTR_CHEMISTRY', CTR_CHEMISTRY)
    # print('CTR_DUPS', CTR_DUPS)
    # print('CTR_ONLY_PUNC_CHANGED', CTR_ONLY_PUNC_CHANGED)
    # print('CTR_INVALID_NUM_CHANGED_SENTS', CTR_INVALID_NUM_CHANGED_SENTS)
    # print('CTR_NON_EDIT_CHUNKS', CTR_NON_EDIT_CHUNKS)
    # print('CTR_EDIT_CHANGED_NUM_SENTS', CTR_EDIT_CHANGED_NUM_SENTS)
    # print('CTR_FAILED_TAGGING', CTR_FAILED_TAGGING)
