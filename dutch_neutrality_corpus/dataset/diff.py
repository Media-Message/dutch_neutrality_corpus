import re
import logging
import unidecode

from bs4 import BeautifulSoup
from nltk import sent_tokenize
from nltk import word_tokenize

from dutch_neutrality_corpus.dataset.text import text_sanitation
from dutch_neutrality_corpus.dataset.retrieve import (
    get_wikipedia_revision_url)

NODE_REGEX = re.compile(
    r'(diff-deletedline)|(diff-addedline)|(diff-empty)')
DIV_REGEX = re.compile(r'<div.*?>(.*)</div>', re.DOTALL)

EMPTY_DIV_REGEX = re.compile(r'(diff-empty)')
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

IMAGE_SUFFIX_REGEX = r'.jpeg|.svg|.jpg|.png'

# TODO: remove from nodes...
# "De neutraliteit van dit artikel is
# [[Wikipedia:Onenigheid over de neutraliteit|omstreden]].""

# TODO: ignore title changes?
# i.e. == Jesus in the [[Quran]] ==


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
    # Convert accented words
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
        # text = annotated_terms.strip()
        text = annotated_terms.replace(SPLIT_TOKEN, '')\
            .replace(START_TOKEN, '')\
            .replace(END_TOKEN, '')\
            .replace('\n', '')
        text = html_sanitization(text)
        return text

    def convert_text_to_tokens(self, text):
        return word_tokenize(text)

    def length(self):
        return len(self.text)

    def get_label_mask(self, tokens):
        return [self.label] * len(tokens)

    def is_valid(self):
        # If any characters exist after cleaning
        if self.text.strip():
            return True
        return False


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

    def get_wikipedia_url(self):
        return get_wikipedia_revision_url(self.revision_id)

    def convert_sentence_to_spans(self, annotated_text):
        split_terms = annotated_text.split(SPLIT_TOKEN)

        spans = []
        for terms in split_terms:

            # Ignore empty strings
            if not terms:
                continue

            label = 0
            if self.is_revision:
                label = 0
            elif (START_TOKEN in terms) or (END_TOKEN in terms):
                label = 1

            span = Span(annotated_terms=terms, label=label)

            if span.is_valid():
                spans.append(span)

        return spans

    def get_npov_labels(self):
        npov_labels = []
        span_count = len(self.spans)
        length_counter = 0
        for idx, span in enumerate(self.spans):

            if idx > 0 and idx < span_count:
                length_counter += 1

            start_index = length_counter
            end_index = length_counter + span.length()
            length_counter += span.length()

            if span.label == 1:
                label = [start_index, end_index, 'SUBJ']
                npov_labels.append(label)

        return npov_labels

    def create_corpus_example(self):
        return {
            'text': self.get_text(),
            'tokens': self.get_tokens(),
            'labels': self.get_npov_labels(),
            'label_masks': self.get_label_masks(),
            'is_revision': self.is_revision,
            'revision_id':  self.revision_id,
            'revision_url': self.get_wikipedia_url()
        }


def contains_image_reference(text):
    response = False
    if re.search(IMAGE_SUFFIX_REGEX, text):
        response = True
    return response


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

        if contains_image_reference(text=sentence):
            # Ignore images
            continue

        sentence_object = \
            Sentence(
                annotated_text=sentence,
                revision_id=revision_id,
                is_revision=is_revision)

        example = sentence_object.create_corpus_example()

        # Ignore empty sentences
        if example.get('text'):
            examples.append(example)

    return examples


def is_empty_div(node):
    return re.match(
        EMPTY_DIV_REGEX,
        node.div.prettify(formatter=None))


def replace_span_tag_with_split_tokens(annotated_text, is_revision=False):
    inner_tag = '<del class="diffchange diffchange-inline">'
    outer_tag = '</del>'

    if is_revision:
        inner_tag = '<ins class="diffchange diffchange-inline">'
        outer_tag = '</ins>'

    return annotated_text.replace(
        inner_tag,
        f'{SPLIT_TOKEN}{START_TOKEN}')\
        .replace(
            outer_tag,
            f'{END_TOKEN}{SPLIT_TOKEN}')


def extract_example_from_node(node,
                              regex,
                              revision_id,
                              is_revision):
    # TODO: change to match rather...
    prior_deleted_spans_list = \
        extract_spans(
            node=node,
            regex=regex)

    if not prior_deleted_spans_list:
        # Nothing to extract
        return {}

    div = parse_div_from_node(node=node)

    annotated_div = \
        replace_span_tag_with_split_tokens(
            annotated_text=div,
            is_revision=is_revision)

    examples = \
        convert_annotated_text_to_corpus(
            annotated_div,
            revision_id=revision_id,
            is_revision=is_revision)

    return examples


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

            if is_empty_div(node=prior_node):
                print('Ignoring: empty prior div')
                continue

            examples = \
                extract_example_from_node(
                    node=prior_node,
                    regex=DELETED_INLINE_REGEX,
                    revision_id=revision_id,
                    is_revision=False)

            if examples:
                corpus.extend(examples)

        if post_node.div:

            if is_empty_div(node=post_node):
                print('Ignoring: empty post div')
                continue

            examples = \
                extract_example_from_node(
                    node=post_node,
                    regex=ADDED_INLINE_REGEX,
                    revision_id=revision_id,
                    is_revision=True)

            if examples:
                corpus.extend(examples)

        if post_added_spans_list and not prior_deleted_spans_list:
            # TODO: add matching sentence for only deleted words...
            # Prior has words deleted and no words added in post
            # Find most similar sentence to edited sentence in prior
            pass

        return corpus

# TODO: consider...
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
