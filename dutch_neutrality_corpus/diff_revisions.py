import re
import sys
import logging
import string
from urllib.request import urlopen
import unidecode
from typing import List, NamedTuple

import spacy
from bs4 import BeautifulSoup
from nltk import sent_tokenize
from nltk import word_tokenize

from dutch_neutrality_corpus.process_text import text_sanitation

NODE_REGEX = re.compile(
    r'(diff-deletedline)|(diff-addedline)|(diff-empty)')
DIV_REGEX = re.compile(r'<div.*?>(.*)</div>', re.DOTALL)

CHANGE_INLINE_REGEX = re.compile(r'(diffchange-inline)')
DELETED_INLINE_REGEX = \
    '<del class="diffchange diffchange-inline">(.*?)</del>'
ADDED_INLINE_REGEX = \
    '<ins class="diffchange diffchange-inline">(.*?)</ins>'

SPLIT_TOKEN = '<SPLIT>'
START_TOKEN = '<EDIT-START>'
END_TOKEN = '<EDIT-END>'

INNER_TOKEN_REGEX = re.compile(r'<EDIT-START>(.*)<EDIT-END>', re.DOTALL)

START_TOKEN_LENGTH = len(START_TOKEN)
END_TOKEN_LENGTH = len(END_TOKEN)

# TODO: use larger model in experiments...
nlp = spacy.load('nl_core_news_sm')

# TODO: remove from nodes...
# "De neutraliteit van dit artikel is
# [[Wikipedia:Onenigheid over de neutraliteit|omstreden]].""

# TODO: ignore title changes?
# i.e. == Jesus in the [[Quran]] ==


# def get_token_indices_of_text_span(text):

#     matches = re.finditer(INNER_TOKEN_REGEX, text)


#     spans = []
#     for match in matches:
#         start_index = match.start() + START_TOKEN_LENGTH
#         end_index = match.end() - END_TOKEN_LENGTH
#         span = {
#             'start_index': start_index
#             'end_index': end_index
#         }

#     return start, end

def is_index_in_list(index, l):
    return index < len(l)


# def create_text_spans(sentence_tokens, label_mask):

#     # TODO: refactor...
#     spans_indices = []
#     sentence = ''

#     for (word, label) in zip(sentence_tokens, label_mask):

#         if label == 1:
#             start_index = len(sentence)

#             # Account for space added during later join
#             if start_index > 0:
#                 start_index += 1

#             end_index = start_index + len(word)

#             spans_indices.append({
#                 'start': start_index,
#                 'end': end_index
#             })

#         sentence = ' '.join([sentence, word])

#     merged_spans = []
#     start_counter = None
#     for list_idx, span in enumerate(spans_indices):
#         current_start_index, current_end_index = span[0], span[1]

#         previous_list_idx = list_idx - 1
#         if is_index_in_list(previous_list_idx, spans_indices):
#             previous_start_index, previous_end_index = span[0], span[1]

#         spans_indices.append(
#             [start_index, end_index, 'SUBJ']
#         )

#     return text, spans


def parse_nodes_from_html(html_content):
    soup = BeautifulSoup(html_content, features='html.parser')
    nodes = soup.find_all(class_=NODE_REGEX)
    return nodes


def parse_div_from_node(node):
    result = re.match(
        DIV_REGEX,
        node.div.prettify(formatter=None))

    if result:
        result = result.group(1).strip()

    return result


def contains_inline_change(node):
    node = node.div.prettify(formatter=None)
    if CHANGE_INLINE_REGEX.search(node):
        return True
    return False


def extract_spans(node, regex):
    text = node.div.prettify(formatter=None)
    text = text.replace('\n', ' ')
    matches = re.findall(regex, text)
    return [m.strip() for m in matches]


def html_sanitization(text):
    # TODO: convert accented words instead of removing
    text = unidecode.unidecode(text)
    text = text_sanitation(text)
    return text.replace('.', '').strip()


def convert_to_tokens_and_labels(terms, label=0):
    # Clean text
    terms = html_sanitization(terms)

    # Word tokenise
    terms_tokens = word_tokenize(terms)

    # Generate 0/1's label mask of length sentence
    mask = [label] * len(terms_tokens)
    return mask, terms_tokens


class Span():

    def __init__(self,
                 annotated_terms,
                 label,
                 start=None,
                 end=None):
        self.annotated_terms = annotated_terms
        self.label = label
        self.start = start
        self.end = end
        self.text = self.convert_annotated_text_to_text(annotated_terms)
        self.tokens = self.convert_text_to_tokens(self.text)
        self.label_mask = self.get_label_mask(self.tokens)

    def convert_annotated_text_to_text(self, annotated_terms):
        text = annotated_terms.replace(SPLIT_TOKEN, '')\
            .replace(START_TOKEN, '')\
            .replace(END_TOKEN, '')
        return html_sanitization(text)

    def convert_text_to_tokens(self, text):
        return word_tokenize(text)

    def length(self):
        return len(self.text)

    def get_label_mask(self, tokens):
        return [self.label] * len(self.tokens)


class Sentence():

    def __init__(self,
                 annotated_text,
                 revision_id,
                 is_revision=False):
        self.annotated_text = annotated_text
        self.revision_id = revision_id
        self.is_revision = is_revision
        self.spans = self.convert_sentence_to_spans(annotated_text)

    def get_text(self):
        return ' '.join([span.text for span in self.spans])

    def get_tokens(self):
        return [t for span in self.spans for t in span.tokens]

    def get_label_masks(self):
        return [m for span in self.spans for m in span.label_mask]

    def convert_sentence_to_spans(self, annotated_text):
        split_terms = annotated_text.split(SPLIT_TOKEN)

        spans = []
        for terms in split_terms:

            label = 0
            if self.is_revision:
                label = 0
            elif (START_TOKEN in terms) or (END_TOKEN in terms):
                label = 1

            spans.append(
                Span(annotated_terms=terms, label=label)
            )

        return spans

    def get_npov_labels(self):
        npov_labels = []
        span_count = len(self.spans)
        length_counter = 0
        for idx, span in enumerate(self.spans):

            start_index = length_counter
            end_index = length_counter + span.length()
            length_counter += span.length()

            if idx > 0 and idx < span_count:
                length_counter += 1

            if span.label == 1:
                npov_labels.append(
                    [start_index, end_index, 'SUBJ']
                )

        return npov_labels

    def convert_spans_to_corpus_example(self, spans):
        return {
            'text': self.get_text(),
            'tokens': self.get_tokens(),
            'labels': self.get_npov_labels(),
            'label_masks': self.get_label_masks(),
            'is_revision': self.is_revision
        }

    def create_corpus_example(self):
        spans = self.convert_sentence_to_spans(self.annotated_text)
        corpus_example = self.convert_spans_to_corpus_example(spans)
        return corpus_example

# TODO: create AnnotatedText object...


def convert_annotated_text_to_corpus(
        annotated_text,
        revision_id,
        is_revision=False):

    # TODO: classify each deleted span...
    # i.e. valid, link change, etc.
    sentences = sent_tokenize(annotated_text)

    examples = []
    for sentence in sentences:

        if SPLIT_TOKEN not in sentence:
            # TODO: consider adding as unbiased...
            continue

        sentence_object = \
            Sentence(
                annotated_text=sentence,
                revision_id=revision_id,
                is_revision=is_revision)

        example = sentence_object.create_corpus_example()
        examples.append(example)

    return examples


# def convert_annotated_text_to_corpus_examples(
#         annotated_text,
#         is_revision=False):

#     # TODO: classify each deleted span...
#     # i.e. valid, link change, etc.
#     sentences = sent_tokenize(annotated_text)

#     sentence_tokens = []
#     label_masks = []
#     original_sentences = []
#     for sentence in sentences:

#         if SPLIT_TOKEN not in sentence:
#             # TODO: consider adding as unbiased...
#             continue

#         terms_list = []
#         label_mask = []

#         is_inner_sentence_span = \
#             (START_TOKEN in sentence and
#                 END_TOKEN in sentence)

#         is_start_of_multi_sentence_span = \
#             (START_TOKEN in sentence and
#                 END_TOKEN in sentence)

#         is_end_of_multi_sentence_span = \
#             (START_TOKEN not in sentence and
#                 END_TOKEN in sentence)

#         split_prior_terms = sentence.split(SPLIT_TOKEN)

#         for terms in split_prior_terms:

#             if is_revision:
#                 label = 0
#             elif (is_inner_sentence_span and
#                     (START_TOKEN not in terms)):
#                 label = 0
#             elif (is_start_of_multi_sentence_span and
#                     (START_TOKEN not in terms)):
#                 label = 0
#             elif (is_end_of_multi_sentence_span and
#                     (END_TOKEN not in terms)):
#                 label = 0
#             else:
#                 # Contains edit
#                 label = 1

#             terms = terms.replace(START_TOKEN, '')
#             terms = terms.replace(END_TOKEN, '')

#             mask, term_tokens = \
#                 convert_to_tokens_and_labels(
#                     terms=terms,
#                     label=label)

#             terms_list.extend(term_tokens)
#             label_mask.extend(mask)

#         sentence_tokens.append(terms_list)
#         label_masks.append(label_mask)
#         original_sentences.append(
#             sentence.replace(SPLIT_TOKEN, '')
#             .replace(START_TOKEN, '')
#             .replace(END_TOKEN, '')
#         )

#     return sentence_tokens, label_masks, original_sentences


# def create_corpus_example(sentence_tokens,
#                           label_masks,
#                           original_sentences,
#                           revision_id,
#                           category):
#     tokens_labels_sentences = \
#         zip(sentence_tokens, label_masks, original_sentences)
#     examples = [
#         {
#             'revision_id': revision_id,
#             'sentence_tokens': t,
#             'label_mask': l,
#             'original_sentence': s,
#             'category': category
#         } for t, l, s in tokens_labels_sentences
#     ]

#     return examples


def extract_examples(html_content, revision_id):

    nodes = parse_nodes_from_html(html_content=html_content)

    corpus = []
    # Iterate over pairs of prior and post texts
    for i in range(0, len(nodes), 2):

        # skip straddeling cases
        if i + 1 >= len(nodes):
            continue

        prior_node = nodes[i]
        post_node = nodes[i + 1]

        # TODO: ignore diff-context for prior and post

        prior_deleted_spans_list = []
        post_added_spans_list = []

        if prior_node.div:

            EMPTY_DIV_REGEX = re.compile(r'(diff-empty)')
            is_empty_div = re.match(
                EMPTY_DIV_REGEX,
                prior_node.div.prettify(formatter=None))

            if is_empty_div:
                print('Ignoring: empty prior div')
                continue

            prior_deleted_spans_list = extract_spans(
                node=prior_node,
                regex=DELETED_INLINE_REGEX)

            prior_div = parse_div_from_node(node=prior_node)

            annotated_prior_div = \
                prior_div.replace(
                    '<del class="diffchange diffchange-inline">',
                    f'{SPLIT_TOKEN}{START_TOKEN}')\
                .replace(
                    '</del>',
                    f'{END_TOKEN}{SPLIT_TOKEN}')

            print('annotated_prior_div: ', annotated_prior_div)

        if post_node.div:

            EMPTY_DIV_REGEX = re.compile(r'(diff-empty)')
            is_empty_div = re.match(
                EMPTY_DIV_REGEX,
                post_node.div.prettify(formatter=None))

            if is_empty_div:
                print('Ignoring: empty post div')
                continue

            post_added_spans_list = extract_spans(
                node=post_node,
                regex=ADDED_INLINE_REGEX)

            post_div = parse_div_from_node(node=post_node)

            annotated_post_div = \
                post_div.replace(
                    '<ins class="diffchange diffchange-inline">',
                    f'{SPLIT_TOKEN}{START_TOKEN}')\
                .replace(
                    '</ins>',
                    f'{END_TOKEN}{SPLIT_TOKEN}')

            print('annotated_post_div: ', annotated_post_div)

        if prior_deleted_spans_list:

            examples = \
                convert_annotated_text_to_corpus(
                    annotated_prior_div,
                    revision_id=revision_id,
                    is_revision=False)

            corpus.extend(examples)

        if post_added_spans_list:

            examples = \
                convert_annotated_text_to_corpus(
                    annotated_prior_div,
                    revision_id=revision_id,
                    is_revision=True)

            corpus.extend(examples)

        if prior_deleted_spans_list and not prior_deleted_spans_list:
            # TODO: match for only deleted words...
            # Prior has words deleted and no words added in post
            # Find most similar sentence to edited sentence in prior
            pass

        print('corpus: ', corpus)

        return corpus

# if not prior_deleted_spans_list:
#     # Only added words or sentences -> inspect...
#     pass
# elif prior_deleted_spans_list and (not post_added_spans_list):
#     # Only deleted exist -> treat as biased
#     pass
# elif prior_deleted_spans_list:
#     pass


# TODO: consider lexicon of dutch subjective words...wiki...


def apply_example_extraction(row):
    revision_id = row['revision_id']
    html_content = row['html_content']

    revision_wiki_url = f'https://nl.wikipedia.org/wiki/?diff={revision_id}'

    logging.info(f'Processing revision_id={revision_id} : {revision_wiki_url}')

    corpus = extract_examples(
        html_content=html_content,
        revision_id=revision_id)

    return corpus


def html2diff(html):
    prior_changed, post_changed = [], []
    prior_deleted, post_added = [], []

    nodes = parse_nodes_from_html(html_content=html)

    # print('Number of nodes: ', len(nodes))
    # print(nodes)

    # Iterate over pairs of prior and post texts
    for i in range(0, len(nodes), 2):

        # skip straddeling cases
        if i + 1 >= len(nodes):
            continue

        prior_node = nodes[i]
        post_node = nodes[i + 1]

        # print('node_prior: ', prior_node)
        # print('node_post: ', post_node)

        # seperate revisions into chunks that were modified,
        # chunks that were purely deleted and chunks that were purely added

        # TODO: rather parse div then perform if statements...

        # No prior and post chunk
        if not prior_node.div and not post_node.div:
            continue

        # Only added chunk
        elif not prior_node.div:
            post_match = parse_div_from_node(node=post_node)

            if post_match:
                post_added.append(post_match)

        # Only deleted chunk
        elif not post_node.div:
            prior_match = parse_div_from_node(node=prior_node)

            if prior_match:
                prior_deleted.append(prior_match)

        # Modified chunks
        else:
            prior_match = parse_div_from_node(node=prior_node)
            post_match = parse_div_from_node(node=post_node)

            if prior_match and post_match:
                prior_changed.append(prior_match)
                post_changed.append(post_match)

    # print()
    # print('* prior_changed: ', prior_changed)
    # print('* post_changed: ', post_changed)
    # print('* prior_deleted: ', prior_deleted)
    # print('* post_added: ', post_added)

    return prior_changed, post_changed, prior_deleted, post_added


def url2diff(url):
    try:
        response = urlopen(url)
        html = response.read()
        return html2diff(html)
    except Exception as e:
        print(e, file=sys.stderr)
        return [], [], [], []


def wiki_text_clean(text):
    text = ''.join([x for x in text if x in string.printable])
    text = text.replace('\n', ' ').replace('\t', ' ')
    return text


def diff_single_revision(row):
    revision_id = row['revision_id']
    html_content = row['html_content']

    revision_wiki_url = \
        f'https://nl.wikipedia.org/wiki/?diff={revision_id}'

    logging.info(f'Processing revision_id={revision_id} : {revision_wiki_url}')

    print(f'Processing revision_id={revision_id}')
    prior_, post_, prior_deleted, post_added = \
        html2diff(html=html_content)

    # TODO: add later...
    # if len(prevs_) != len(nexts_):
    #     logging.info('ERROR: corpus sizes not equal!')
    #     continue

    prior, post = [], []

    for prior_text, post_text in zip(prior_, post_):
        prior.append(wiki_text_clean(prior_text))
        post.append(wiki_text_clean(post_text))

    prior_deleted = \
        [wiki_text_clean(prior_text) for prior_text in (
            prior_deleted or ['no_deleted_chunks'])]
    post_added = \
        [wiki_text_clean(post_text) for post_text in (
            post_added or ['no_added_chunks'])]

    return {
        'revision_id': revision_id,
        'prior': prior,
        'post': post,
        'prior_deleted': prior_deleted,
        'post_added': post_added
    }

# Legacy Code:


# def html2diff(html):
#     prev_changed, next_changed = [], []
#     prev_deleted, next_added = [], []

#     soup = BeautifulSoup(html, features='html.parser')

#     nodes = soup.find_all(class_=re.compile(
#         r'(diff-deletedline)|(diff-addedline)|(diff-empty)'))

#     DIV_P = re.compile(r'<div.*?>(.*)</div>', re.DOTALL)

#     for i in range(0, len(nodes), 2):

#         # skip straddeling cases
#         if i + 1 >= len(nodes):
#             continue

#         node_prev = nodes[i]
#         node_next = nodes[i + 1]

#         # seperate revisions into chunks that were modified,
#         # chunks that were purely deleted and chunks that were purely added
#         if not node_prev.div and not node_next.div:
#             continue

#         # Purely added chunk
#         elif not node_prev.div:
#             next_match = re.match(
#                 DIV_P,
#                 node_next.div.prettify(formatter=None))

#             if next_match:
#                 next_added.append(next_match.group(1).strip())

#         # Purely deleted
#         elif not node_next.div:
#             prev_match = re.match(
#                 DIV_P,
#                 node_prev.div.prettify(formatter=None))

#             if prev_match:
#                 prev_deleted.append(prev_match.group(1).strip())

#         # Modified chunk
#         else:
#             prev_match = re.match(
#                 DIV_P, node_prev.div.prettify(formatter=None))
#             next_match = re.match(
#                 DIV_P, node_next.div.prettify(formatter=None))

#             if prev_match and next_match:
#                 prev_changed.append(prev_match.group(1).strip())
#                 next_changed.append(next_match.group(1).strip())

#     return prev_changed, next_changed, prev_deleted, next_added
