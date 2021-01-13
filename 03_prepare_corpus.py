#!/usr/bin/env python3
import logging
import argparse
import multiprocessing

import pandas as pd

from src.pipeline import Pipeline, Stage
from src.revision_processing import (
    apply_revision_processing
)
from src.utils import (
    LoadCSVStage,
    SaveIterableToCSVStage
)


logging.basicConfig(level='INFO')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Extract revision IDs from wiki meta history dump.')
    parser.add_argument('--revisions-text-file',
                        type=str,
                        # nargs=1,
                        required=True,
                        help='filepath to revision text file')
    parser.add_argument('--output-file',
                        type=str,
                        required=False,
                        default='revisions_processed_text.csv',
                        help='filepath for processed text')
    parser.add_argument('--model-cache',
                        type=str,
                        required=False,
                        default='bert-base-uncased-model',
                        help='filepath for cached BERT model')
    parser.add_argument('--output-prefix',
                        type=str,
                        required=False,
                        default='revisions-data',
                        help='filepath prefix for output files')

    args = parser.parse_args()
    revisions_text_file = str(args.revisions_text_file)
    output_file = str(args.output_file)
    model_cache = str(args.model_cache)
    output_prefix = str(args.output_prefix)

    columns = ['revision_id', 'prior', 'post', 'prior_deleted', 'post_added']
    stages = [
        LoadCSVStage(
            filepath=revisions_text_file,
            select_columns=columns,
            return_type='list_of_dicts'
        ),
        Stage(func=apply_revision_processing),
        SaveIterableToCSVStage(filepath=output_prefix)
    ]

    pipeline = Pipeline(stages=stages)
    results = pipeline.run(collection=None)

    # print(list(results))
    # # De-duplicate
    # seen_examples = set()
    # tmp = []
    # for ex in results:
    #     if ex['out_row'] in seen_examples:
    #         continue
    #     else:
    #         tmp += [ex]
    #         seen_examples.add(ex['out_row'])

    # out = tmp

    # # ratio thresholding
    # ratios = [x['length_ratio'] for x in out if x['is_word_edit'] is not None]
    # N = len(ratios) * 1.0
    # mu = np.mean(ratios)
    # sd = np.std(ratios)

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
