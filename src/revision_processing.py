#!/usr/bin/env python3
import math
import re
# import random
import logging
# from itertools import groupby
from collections import Counter

# from spellchecker import SpellChecker

# from autocorrect import spell
from simplediff import diff
import Levenshtein
from nltk import sent_tokenize, word_tokenize

from src.text_processing import (
    apply_text_sanitation,
    apply_bert_tokenization
)

logging.basicConfig(level='INFO')

# TODO: refactor...


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

# TODO: refactor...


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


def get_token_labels(s_diff):
    tok_labels = []
    for tag, chunk in s_diff:
        if tag == '=':
            tok_labels += [0] * len(chunk)

        elif tag == '-':
            tok_labels += [1] * len(chunk)

        else:
            pass

    return tok_labels


def is_single_word_edit(d):
    """ is this diff good for the final generation dataset """
    pre_chunks = [chunk for tag, chunk in d if tag == '-']
    post_chunks = [chunk for tag, chunk in d if tag == '+']

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
    prei = next((i for i, x in enumerate(d) if x[0] == '-'))
    if prei < len(d) - 1 and d[prei + 1][0] == '+':
        return True

# TODO: refactor to pipeline...


def should_keep(
        prior_raw,
        prior_tokens,
        post_raw,
        post_tokens,
        bleu_score,
        revision_id):

    # KEEP -- exact match
    if bleu_score == 100 or prior_raw == post_raw:
        length_prior = len(prior_tokens.split())
        return True, None, [0 for _ in range(length_prior)]

    # clearly not a match
    if bleu_score < 15.0:
        # CTR_LOW_BLEU += 1
        logging.info(f'Low BLEU: {bleu_score}')
        return False, None, None

    # too close
    levenshtein_distance = Levenshtein.distance(
        prior_tokens,
        post_tokens)

    if levenshtein_distance < 4:
        # CTR_LOW_LEVEN += 1
        logging.info(f'Low Levenstein: {levenshtein_distance}')
        return False, None, None

    token_diff = diff(
        prior_tokens.split(),
        post_tokens.split()
    )

    token_labels = get_token_labels(token_diff)
    assert len(token_labels) == len(prior_tokens.split())

    changed_text = ''.join(
        [''.join(chunk) for tag, chunk in token_diff if tag != '=']
    )

    if not re.search('[a-z]', changed_text):
        # CTR_ONLY_PUNC_CHANGED += 1
        logging.info('Only punctuation changed')
        return False, None, None

    # too dissimilar -- less than half of tokens shared
    tok_nums = [int(x) for x in token_labels]
    if (sum(tok_nums) * 1.0 / len(tok_nums)) > 0.5:
        # CTR_TOO_MANY_1_TOKS += 1
        logging.info('Too dissimilar -- less than half of toks shared')
        return False, None, None

    # edit was just fixing a spelling error
    word_diff = diff(
        word_tokenize(prior_raw),
        word_tokenize(post_raw)
    )

    # if is_spelling_diff(word_diff):
    #     CTR_SPELLING += 1
    #     return False, None, None

    # some simple filtering to get out the chemistry "neutral" edits
    if (' molecules' in prior_raw or
        ' ions' in prior_raw or
        ' ionic' in prior_raw or
            ' atoms' in prior_raw):
        # CTR_CHEMISTRY += 1
        logging.info('Chemistry "neutral" edits')
        return False, None, None

    # # use enchant to make sure example has enough normal words
    # prior_words = prior_words.translate(str.maketrans(
        # '', '', string.punctuation)).split()
    # n_words = sum(1 if d.check(w) else 0 for w in pre_words)
    # if len(prior_words) == 0 or (float(n_words) / len(prior_words)) < 0.5:
    #     return False, None, None

    # see if this is a "single word" edit,
    # where a single word was replaced with 0+ words
    single_word_edit = is_single_word_edit(word_diff)

    return True, single_word_edit, token_labels


def apply_revision_processing(revision):

    # revision_id, prior, post, prior_deleted, post_added = revision
    revision_id = revision['revision_id']
    prior = revision['prior']
    post = revision['post']
    prior_deleted = revision['prior_deleted']
    post_added = revision['post_added']

    # empty revision
    if not prior or not post:
        # CTR_EMPTY_REV += 1
        logging.info('Empty revision')
        # return None

    if (prior_deleted != ['no_deleted_chunks'] or
            post_added != ['no_added_chunks']):
        # CTR_NON_EDIT_CHUNKS += 1
        logging.info('Non-edited chunks')

    # logging.info('revision_id: ', revision_id)
    # logging.info('prior1: ', prior)

    # unicode
    if isinstance(prior[0], bytes):
        prior = [x.decode() for x in prior]

    if isinstance(post[0], bytes):
        post = [x.decode() for x in post]

    # multiple edits
    if len(prior) > 1 or len(post) > 1:
        # CTR_MULTIPLE_EDITS += 1
        logging.info('Multiple edits')

    prior_text = apply_text_sanitation(prior)
    post_text = apply_text_sanitation(post)

    logging.info('prior_text: ', prior_text)
    logging.info('post_text: ', post_text)

    # failed cleaning
    if not prior_text or not post_text:
        # CTR_FAILED_CLEANING += 1
        logging.info('Failed cleaning')

    prior_sentence_raw = sent_tokenize(prior_text)
    post_sentence_raw = sent_tokenize(post_text)

    prior_sentence_raw = \
        [s.replace("'", '').strip() for s in prior_sentence_raw]
    post_sentence_raw = \
        [s.replace("'", '').strip() for s in post_sentence_raw]

    logging.debug('prior_sentence_raw: ', prior_sentence_raw)
    logging.debug('post_sentence_raw: ', post_sentence_raw)

    if len(prior_sentence_raw) != len(post_sentence_raw):
        # CTR_EDIT_CHANGED_NUM_SENTS += 1
        logging.info('Edit changed number of sentences')

    prior_sentence_tokens = \
        [apply_bert_tokenization(s) for s in prior_sentence_raw]
    post_sentence_tokens = \
        [apply_bert_tokenization(s) for s in post_sentence_raw]

    logging.debug('prior_sentence_tokens: ', prior_sentence_tokens)
    logging.debug('post_sentence_tokens: ', post_sentence_tokens)

    matches = find_matches(prior_sentence_tokens, post_sentence_tokens)

    # TODO: refactor later...
    processed_revisions = []
    for i, j, bleu_score in matches:

        # TODO: Rename function later...
        keep, is_word_edit, token_labels = should_keep(
            prior_raw=prior_sentence_raw[i],
            prior_tokens=prior_sentence_tokens[i],
            post_raw=post_sentence_raw[j],
            post_tokens=post_sentence_tokens[j],
            bleu_score=bleu_score,
            revision_id=revision_id
        )

        if not keep:
            logging.info(
                f'Not keeping: revision_id={revision_id}')
            continue

        length_ratio = \
            len(prior_sentence_raw[i]) * 1.0 / len(post_sentence_raw[j])

        # TODO: Change to dict later...
        processed_revisions.append(
            {
                'revision_id': revision_id,
                'bleu_score': bleu_score,
                'is_word_edit': is_word_edit,
                'token_labels': token_labels,
                'length_ratio': length_ratio,
                'prior_sentence_raw': prior_sentence_raw[i],
                'prior_sentence_tokens': prior_sentence_tokens[i],
                'post_sentence_raw': post_sentence_raw[j],
                'post_sentence_tokens': post_sentence_tokens[j]
            }
        )

    # only take revisions where a single sentence was changed
    # if sum([sum(x[-1]) > 0 for x in rev_examples]) != 1:
    #     CTR_INVALID_NUM_CHANGED_SENTS += \
    #   len([x for x in rev_examples if sum(x[-1]) > 0])
    #     continue

    # ignore the revision if duplicates got in the mix somehow
    # revision_prior = [x[0] for x in processed_revisions]
    # revision_post = [x[2] for x in processed_revisions]

    # if (len(revision_prior) != len(set(revision_prior)) or
    #         len(revision_post) != len(set(revision_post))):
    #     # CTR_DUPS += len([x for x in rev_examples if sum(x[-1]) > 0])
    #     logging.info('Duplicate')
    #     # return None

    return processed_revisions
