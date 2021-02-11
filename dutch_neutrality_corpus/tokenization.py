import logging

from nltk import sent_tokenize
from pytorch_pretrained_bert.tokenization import BertTokenizer

logging.basicConfig(
    level='INFO',
    format='%(asctime)s %(message)s',
    filename='dwnc.log')

# TODO: change to dutch...
BERT_MODEL = 'bert-base-uncased'
BERT_CACHE = 'bert-base-uncased-model'
BERT_TOKENIZER = BertTokenizer.from_pretrained(
    BERT_MODEL,
    cache_dir=BERT_CACHE)


def sentence_tokenization(text):
    tokens = sent_tokenize(text)
    return [t.replace("'", '').strip() for t in tokens]


def bert_tokenization(text):
    # text = ' '.join(text).strip()
    text = text.strip()
    token_list = BERT_TOKENIZER.tokenize(text)
    return ' '.join(token_list)


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
