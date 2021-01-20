#!/usr/bin/env python3
import math
import re
import logging
from collections import Counter

import numpy as np
from simplediff import diff
import Levenshtein
from nltk import word_tokenize

logging.basicConfig(level='INFO')


def calculate_bleu_score(hyp, ref):

    # get ngram stats
    stats = []
    stats.append(len(hyp))
    stats.append(len(ref))

    for n in range(1, 5):
        s_ngrams = Counter(
            [tuple(hyp[i:i + n]) for i in range(len(hyp) + 1 - n)]
        )
        r_ngrams = Counter(
            [tuple(ref[i:i + n]) for i in range(len(ref) + 1 - n)]
        )
        stats.append(max([sum((s_ngrams & r_ngrams).values()), 0]))
        stats.append(max([len(hyp) + 1 - n, 0]))

    # get bleu from stats
    if len(list(filter(lambda x: x == 0, stats))) > 0:
        return 0

    (c, r) = stats[:2]

    log_bleu_prec = sum(
        [math.log(float(x) / y) for x, y in zip(stats[2::2], stats[3::2])]
    ) / 4.

    bleu = math.exp(min([0, 1 - float(r) / c]) + log_bleu_prec)

    return 100 * bleu


def find_matches(a_list, b_list, delta=3):

    for i in range(len(a_list)):

        min_range = max(i - delta, 0)
        max_range = min(i + delta, len(b_list))

        a_tokens = a_list[i].split()

        neighborhood_bleus = [
            (
                calculate_bleu_score(
                    hyp=a_tokens,
                    ref=b_list[j].split()
                ),
                j
            )
            for j in range(min_range, max_range)
        ]
        # corner case: len(a_list) >> len(b_list)
        if not neighborhood_bleus:
            logging.info('BLEU corner case')
            continue

        max_bleu, match_idx = max(neighborhood_bleus)

        yield i, match_idx, max_bleu

# TODO: find dutch spell checker later...
# def is_spelling_diff(d):
#     """takes a word diff as arg"""
#     global SPELLCHECKER

#     # only look at the one-word diffs
#     if sum([len(chunk) for tag, chunk in d if tag == '-']) > 1:
#         return False

#     for i, (tag, words) in enumerate(d):
#         if (tag == '-' and
#             i+1 < len(d) - 1 and
#             len(words) == 1 and
#               d[i+1][0] == '+'):
#             # is one-word spelling replacement (post correction)
#             correction = spell(words[0])
#             if (not correction == words[0] and
#                   correction in ' '.join(d[i+1][1])):
#                 return True

#     return False


def get_token_labels(token_diff):
    token_labels = []
    for tag, chunk in token_diff:
        if tag == '=':
            token_labels += [0] * len(chunk)

        elif tag == '-':
            token_labels += [1] * len(chunk)

    return token_labels


def is_single_word_edit(word_diff):
    """ is this diff good for the final generation dataset """
    pre_chunks = [chunk for tag, chunk in word_diff if tag == '-']
    post_chunks = [chunk for tag, chunk in word_diff if tag == '+']

    # a single word on the pre side
    if sum([len(chunk) for chunk in pre_chunks]) != 1:
        return False

    # 0 words in the post
    if len(post_chunks) == 0:
        return True

    # ensure 1 post chunk
    if len(post_chunks) > 1:
        return False

    # post language chunk is directly after the pre chunk
    prei = next((i for i, x in enumerate(word_diff) if x[0] == '-'))
    if prei < len(word_diff) - 1 and word_diff[prei + 1][0] == '+':
        return True

# TODO: refactor to pipeline...


def meets_exact_match_criteria(bleu_score, prior, post):
    if (bleu_score == 100 or prior == post):
        return True
    return False


def passes_min_bleu_criteria(bleu_score, min_score=15.0):
    if bleu_score >= min_score:
        return True
    return False


def passes_min_levenshtein_distance_criteria(distance):
    if distance >= 4:
        return True
    return False


def passes_not_only_punctuation_criteria(token_diff):
    changed_text = ''.join(
        [''.join(chunk) for tag, chunk in token_diff if tag != '=']
    )

    if re.search('[a-z]', changed_text):
        return True
    return False


def passes_min_similarity_criteria(token_labels, min_proportion=0.5):
    token_labels = list(map(int, token_labels))
    proportion_of_changed_tokens = (
        sum(token_labels) * 1.0 / len(token_labels))
    if proportion_of_changed_tokens <= min_proportion:
        return True
    return False


def apply_matching_rules(row):

    prior_sentence_raw = row['prior_sentences_raw']
    post_sentence_raw = row['post_sentences_raw']
    prior_sentence_tokens = row['prior_sentences_tokens']
    post_sentence_tokens = row['post_sentences_tokens']
    revision_id = row['revision_id']

    matches = find_matches(
        prior_sentence_tokens,
        post_sentence_tokens)

    corpus = []
    for i, j, bleu_score in matches:

        # Index text and tokens
        prior_raw = prior_sentence_raw[i]
        prior_tokens = prior_sentence_tokens[i]
        post_raw = post_sentence_raw[j]
        post_tokens = post_sentence_tokens[j]

        word_diff = diff(
            word_tokenize(prior_raw),
            word_tokenize(post_raw))

        token_diff = diff(
            prior_tokens.split(),
            post_tokens.split())

        l_distance = Levenshtein.distance(
            prior_tokens,
            post_tokens)

        token_labels = get_token_labels(token_diff)

        # TODO: Add spelling edit check as well

        single_word_edit = is_single_word_edit(word_diff)

        passes_min_bleu = \
            passes_min_bleu_criteria(bleu_score=bleu_score)
        passes_only_punctuation = \
            passes_not_only_punctuation_criteria(token_diff=token_diff)
        passes_min_levenshtein_distance = \
            passes_min_levenshtein_distance_criteria(distance=l_distance)
        passes_min_similarity = \
            passes_min_similarity_criteria(token_labels=token_labels)

        keep = False
        is_word_edit = None
        token_labels = None

        # Exact match
        if meets_exact_match_criteria(
                bleu_score=bleu_score,
                prior=prior_raw,
                post=post_raw):
            logging.info(f'Exact match: {revision_id}')
            keep = True
            is_word_edit = None
            token_labels = token_labels

        # Meets all criteria
        elif (passes_min_bleu or
              passes_only_punctuation or
              passes_min_levenshtein_distance or
                passes_min_similarity):
            keep = True
            is_word_edit = single_word_edit
            token_labels = token_labels

        if not keep:
            logging.info(
                f'Discarding keeping: revision_id={revision_id} index={i}')
            continue

        corpus.append(
            {
                'revision_id': revision_id,
                'bleu_score': bleu_score,
                'is_word_edit': is_word_edit,
                'token_labels': token_labels,
                'prior_sentence_raw': prior_raw,
                'prior_sentence_tokens': prior_tokens,
                'post_sentence_raw': post_raw,
                'post_sentence_tokens': post_tokens
            }
        )

    return corpus


class RowDeduplicationStage():
    """
    De-duplicates iterable given fields to use as unique
    concatenated identifier.
    """

    def __init__(self,
                 deduplication_fields):
        self.deduplication_fields = deduplication_fields

    def create_unique_row_identifier(self, row, fields):
        return ' '.join(
            row[f] for f in fields
        )

    def apply(self, collection):

        unique_rows = set()
        unique_collection = []
        for row in collection:

            unique_row_identifier = \
                self.create_unique_row_identifier(
                    row=row,
                    fields=self.deduplication_fields)

            if unique_row_identifier not in unique_rows:
                # Store unique row in collection
                unique_collection.append(row)
                # Update seen, unique rows
                unique_rows.add(unique_row_identifier)

        return unique_collection


class FilterOnTextLengthStage():
    """
    Filter examples to only contain those in 95th
    percentile with text length.
    """

    def __init__(self,
                 field_a,
                 field_b):
        self.field_a = field_a
        self.field_b = field_b

    def calculate_text_length_statistics(self, collection):
        length_ratios = []
        for row in collection:

            # TODO: why does original filter use word edit??...
            # if row['is_word_edit']:

            # TODO: avoid double calculation of text length...
            # Performance reasons...
            length_ratios.append(
                self.calculate_text_length_ratio(
                    text_a=row[self.field_a],
                    text_b=row[self.field_b]
                )
            )

        mu = np.mean(length_ratios)
        sd = np.std(length_ratios)

        return mu, sd

    def passes_length_criteria(self, x, mu, sd):
        greater_than_upper_bound = (x > mu + 2.0 * sd)
        lower_than_lower_bound = (x < mu - 2.0 * sd)
        if not (greater_than_upper_bound or lower_than_lower_bound):
            return True
        return False

    def calculate_text_length_ratio(self, text_a, text_b):
        return len(text_a) * 1.0 / len(text_b)

    def apply(self, collection):

        mu, sd = \
            self.calculate_text_length_statistics(
                collection=collection)

        new_collection = []
        for row in collection:

            # TODO: avoid double calculation of text length...
            # Performance reasons...
            length_ratio = \
                self.calculate_text_length_ratio(
                    text_a=row[self.field_a],
                    text_b=row[self.field_b])

            if self.passes_length_criteria(length_ratio, mu, sd):
                new_collection.append(row)

        return new_collection


def meets_non_empty_revision_criteria(prior, post):
    if (not prior or not post):
        return False
    return True


def meets_deleted_and_added_criteria(prior_deleted, post_added):
    if (prior_deleted != ['no_deleted_chunks'] or
            post_added != ['no_added_chunks']):
        return False
    return True


def meets_single_edit_criteria(prior, post):
    if len(prior) > 1 or len(post) > 1:
        return False
    return True


def filter_on_first_tier_rules(row,
                               filter_non_empty=False,
                               filter_deleted_and_added=False,
                               filter_single_edit=False):
    prior = row['prior']
    post = row['post']
    prior_deleted = row['prior_deleted']
    post_added = row['post_added']

    is_non_empty_revision = True
    is_deleted_and_added = True
    is_single_edit = True

    if filter_non_empty:
        is_non_empty_revision = \
            meets_non_empty_revision_criteria(
                prior=prior,
                post=post)

    # TODO: evaluate...
    if filter_deleted_and_added:
        is_deleted_and_added = \
            meets_deleted_and_added_criteria(
                prior_deleted=prior_deleted,
                post_added=post_added)

    # TODO: necessary for us?
    if filter_single_edit:
        is_single_edit = \
            meets_single_edit_criteria(
                prior=prior,
                post=post)

    if (is_non_empty_revision and
        is_deleted_and_added and
            is_single_edit):
        return row

    return {}

# Legacy code...

# def apply_revision_processing(revision):

#     # revision_id, prior, post, prior_deleted, post_added = revision
#     revision_id = revision['revision_id']
#     prior = revision['prior']
#     post = revision['post']
#     prior_deleted = revision['prior_deleted']
#     post_added = revision['post_added']

#     # empty revision
#     if not prior or not post:
#         # CTR_EMPTY_REV += 1
#         logging.info('Empty revision')
#         # return None

#     if (prior_deleted != ['no_deleted_chunks'] or
#             post_added != ['no_added_chunks']):
#         # CTR_NON_EDIT_CHUNKS += 1
#         logging.info('Non-edited chunks')

#     # logging.debug('revision_id: ', revision_id)
#     # logging.debug('prior1: ', prior)

#     # unicode
#     if isinstance(prior[0], bytes):
#         prior = [x.decode() for x in prior]

#     if isinstance(post[0], bytes):
#         post = [x.decode() for x in post]

#     # multiple edits
#     if len(prior) > 1 or len(post) > 1:
#         # CTR_MULTIPLE_EDITS += 1
#         logging.info('Multiple edits')

#     prior_text = apply_text_sanitation(prior)
#     post_text = apply_text_sanitation(post)

#     logging.debug('prior_text: ', prior_text)
#     logging.debug('post_text: ', post_text)

#     # failed cleaning
#     if not prior_text or not post_text:
#         # CTR_FAILED_CLEANING += 1
#         logging.info('Failed cleaning')

#     prior_sentence_raw = apply_sentence_tokenize(prior_text)
#     post_sentence_raw = apply_sentence_tokenize(post_text)

#     # prior_sentence_raw = sent_tokenize(prior_text)
#     # post_sentence_raw = sent_tokenize(post_text)

#     # prior_sentence_raw = \
#     #     [s.replace("'", '').strip() for s in prior_sentence_raw]
#     # post_sentence_raw = \
#     #     [s.replace("'", '').strip() for s in post_sentence_raw]

#     logging.debug('prior_sentence_raw: ', prior_sentence_raw)
#     logging.debug('post_sentence_raw: ', post_sentence_raw)

#     if len(prior_sentence_raw) != len(post_sentence_raw):
#         # CTR_EDIT_CHANGED_NUM_SENTS += 1
#         logging.info('Edit changed number of sentences')

#     prior_sentence_tokens = \
#         list(map(apply_bert_tokenization, prior_sentence_raw))
#     post_sentence_tokens = \
#         list(map(apply_bert_tokenization, post_sentence_raw))

#     logging.debug('prior_sentence_tokens: ', prior_sentence_tokens)
#     logging.debug('post_sentence_tokens: ', post_sentence_tokens)

#     matches = find_matches(prior_sentence_tokens, post_sentence_tokens)

#     # TODO: refactor later...
#     processed_revisions = []
#     for i, j, bleu_score in matches:

#         # TODO: Rename function later...
#         keep, is_word_edit, token_labels = should_keep(
#             prior_raw=prior_sentence_raw[i],
#             prior_tokens=prior_sentence_tokens[i],
#             post_raw=post_sentence_raw[j],
#             post_tokens=post_sentence_tokens[j],
#             bleu_score=bleu_score,
#             revision_id=revision_id
#         )

#         if not keep:
#             logging.info(
#                 f'Not keeping: revision_id={revision_id}')
#             continue

#         length_ratio = \
#             len(prior_sentence_raw[i]) * 1.0 / len(post_sentence_raw[j])

#         # TODO: Change to dict later...
#         processed_revisions.append(
#             {
#                 'revision_id': revision_id,
#                 'bleu_score': bleu_score,
#                 'is_word_edit': is_word_edit,
#                 'token_labels': token_labels,
#                 'length_ratio': length_ratio,
#                 'prior_sentence_raw': prior_sentence_raw[i],
#                 'prior_sentence_tokens': prior_sentence_tokens[i],
#                 'post_sentence_raw': post_sentence_raw[j],
#                 'post_sentence_tokens': post_sentence_tokens[j]
#             }
#         )

#     # only take revisions where a single sentence was changed
#     # if sum([sum(x[-1]) > 0 for x in rev_examples]) != 1:
#     #     CTR_INVALID_NUM_CHANGED_SENTS += \
#     #   len([x for x in rev_examples if sum(x[-1]) > 0])
#     #     continue

#     # ignore the revision if duplicates got in the mix somehow
#     # revision_prior = [x[0] for x in processed_revisions]
#     # revision_post = [x[2] for x in processed_revisions]

#     # if (len(revision_prior) != len(set(revision_prior)) or
#     #         len(revision_post) != len(set(revision_post))):
#     #     # CTR_DUPS += len([x for x in rev_examples if sum(x[-1]) > 0])
#     #     logging.info('Duplicate')
#     #     # return None

#     return processed_revisions
