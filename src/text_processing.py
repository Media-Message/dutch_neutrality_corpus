#!/usr/bin/env python3
import string
import re
import logging
import mwparserfromhell

from nltk import sent_tokenize
from pytorch_pretrained_bert.tokenization import BertTokenizer

logging.basicConfig(level='INFO')

# TODO: change to dutch...
BERT_MODEL = 'bert-base-uncased'
BERT_CACHE = 'bert-base-uncased-model'
BERT_TOKENIZER = BertTokenizer.from_pretrained(
    BERT_MODEL,
    cache_dir=BERT_CACHE)

REF_REGEX = r'<ref([-\w=" <>]+)?>.*?<([ ]+)?\/([ ]+)?ref>'
PUNCTUATION = string.punctuation.replace('.', '')


def remove_refs(text):
    text = re.sub(REF_REGEX, ' ', text)

    # leading </ref>
    if '</ref>' in text:
        text = re.sub(REF_REGEX, ' ', '<ref>' + text)

    # trailing <ref>
    if '<ref' in text:
        text = re.sub(REF_REGEX, ' ', text + '</ref>')

    return text


def text_sanitation(text):

    if isinstance(text, list):
        text = ' '.join(text)

    x = text.lower()

    # ascii only
    x = ''.join(filter(lambda x: x in string.printable, x))

    # preemptively remove <ref>'s (including uncomplete)
    x = x.strip()
    x = remove_refs(x)

    # collapse multispaces
    x = re.sub(r'[ ]+', ' ', x)

    parse = mwparserfromhell.parse(x)
    plaintext = parse.strip_code()
    plaintext = remove_refs(plaintext)  # get refs again? some things missed

    # collapse multispaces
    plaintext = re.sub(r'[ ]+', ' ', plaintext)

    # parse again to hit complicatd nested wikicode like 21055249
    parse = mwparserfromhell.parse(plaintext)
    plaintext = parse.strip_code()

    # ignore lines starting with ! or | (likely table artifacts)
    if plaintext.startswith('?') or plaintext.startswith('|'):
        plaintext = ''

    # ignore lines without text, e.g. ( , , , , ) or ]]
    if not re.findall(r'\w', plaintext):
        plaintext = ''

    # parse AGAIN again to hit remaining links e.g. 377258469
    plaintext = plaintext.replace('[ ', '[').replace(' ]', ']')
    parse = mwparserfromhell.parse(plaintext)
    plaintext = parse.strip_code()

    # at this point just remove all brackets
    plaintext = plaintext.replace(']', '').replace('[', '')

    # remove html
    plaintext = re.sub(r'http\S+', '', plaintext)

    # remove parents with nothing in them, e.g. (; )
    plaintext = re.sub(r'\([^\w]*\)', '', plaintext)

    # remove remaining <del>, <ins>
    # (valid tags should already have been taken parsed)
    plaintext = re.sub(r'<\/?(del|ins)([-\w=" <>]+)?>', '', plaintext)

    # remove stars
    plaintext = plaintext.replace('*', '')

    # remove table fragments
    plaintext = re.sub(
        r'(right[ ]?\||left[ ]?\||thumb[ ]?\||frame[ ]?\||\d+px[ ]?\|)',
        '',
        plaintext)

    # ignore timestamp sentences
    if 'retrieved on' in plaintext.lower():
        plaintext = ''

    # msc html missed
    plaintext = plaintext.replace('<blockquote>', '')

    # remove tabs and newlines (those is our deliminators beeyotch)
    plaintext.replace('\t', ' ')
    plaintext.replace('\n', ' ')
    plaintext.replace('\r', '')

    # collapse multispaces (again again)
    plaintext = re.sub(r'[ ]+', ' ', plaintext).strip()

    # Remove punctuation (except period for sentence tokenization)
    plaintext = plaintext.translate(str.maketrans('', '', PUNCTUATION))

    return plaintext


def sentence_tokenization(text):
    tokens = sent_tokenize(text)
    return [t.replace("'", '').strip() for t in tokens]


def bert_tokenization(text):
    # text = ' '.join(text).strip()
    text = text.strip()
    token_list = BERT_TOKENIZER.tokenize(text)
    return ' '.join(token_list)


def apply_text_sanitation(row, apply_to_field, new_field):
    text = row[apply_to_field]

    if isinstance(text, list):
        response = [text_sanitation(text=t) for t in text]
    elif isinstance(text, str):
        response = text_sanitation(text=text)

    # print(response)
    return {
        new_field: response
    }


def apply_sentence_tokenization(row, apply_to_field, new_field):
    text = row[apply_to_field]

    if not text:
        return {
            new_field: text
        }

    if isinstance(text, list):
        text = ' '.join(text)

    response = sentence_tokenization(text=text)

    return {
        new_field: response
    }


def apply_bert_tokenization(row, apply_to_field, new_field):
    text = row[apply_to_field]

    if not text:
        return {
            new_field: text
        }

    response = [bert_tokenization(text=t) for t in text]

    return {
        new_field: response
    }
