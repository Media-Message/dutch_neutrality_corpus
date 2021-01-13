#!/usr/bin/env python3
import string
import re
import logging
import mwparserfromhell

from pytorch_pretrained_bert.tokenization import BertTokenizer

logging.basicConfig(level='INFO')

# TODO: change to dutch...
BERT_MODEL = 'bert-base-uncased'
BERT_CACHE = 'bert-base-uncased-model'
BERT_TOKENIZER = BertTokenizer.from_pretrained(
    BERT_MODEL,
    cache_dir=BERT_CACHE)

REF_REGEX = r'<ref([-\w=" <>]+)?>.*?<([ ]+)?\/([ ]+)?ref>'


def remove_refs(text):
    text = re.sub(REF_REGEX, ' ', text)

    # leading </ref>
    if '</ref>' in text:
        text = re.sub(REF_REGEX, ' ', '<ref>' + text)

    # trailing <ref>
    if '<ref' in text:
        text = re.sub(REF_REGEX, ' ', text + '</ref>')

    return text


def apply_text_sanitation(text):

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

    plaintext = plaintext.translate(
        str.maketrans('', '', string.punctuation))

    return str(plaintext)


def apply_bert_tokenization(text):
    text = text.strip()  # Remove...
    token_list = BERT_TOKENIZER.tokenize(text)
    # TODO: should this happen here? No...
    return ' '.join(token_list)
