#!/usr/bin/env python3
from transformers import TFDistilBertForTokenClassification
import tensorflow as tf
import numpy as np
from transformers import DistilBertTokenizerFast
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer
# from datasets import load_dataset, load_metric

from dutch_neutrality_corpus.io import LoadJSONFileStage


task = "ner"  # Should be one of "ner", "pos" or "chunk"
model_checkpoint = "distilbert-base-uncased"
batch_size = 16

# datasets = load_dataset("conll2003")
# datasets

# label_list = datasets["train"].features[f"{task}_tags"].feature.names

# tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
# print(
#     tokenizer(["Hello", ",", "this", "is", "one", "sentence", "split",
#                "into", "words", "."],
#               is_split_into_words=True)
# )

# TODO: convert to pipeline later...
N_REVISIONS = 10
INPUT_FILE = \
    ('/Users/nicholasmartin/Workspace/OS/dutch_neutrality_corpus'
     '/data/revision_texts_sample.json')

data = LoadJSONFileStage(
    filepath=INPUT_FILE,
    n_revisions=N_REVISIONS
).apply(None)

text_tokens = [row['tokens'] for row in data]
class_labels = [row['class_labels'] for row in data]

print(text_tokens)
print(class_labels)

train_texts, validation_texts, train_labels, validation_labels = \
    train_test_split(
        text_tokens,
        class_labels,
        test_size=.2)

unique_tags = set(tag for doc in class_labels for tag in doc)
tag2id = {tag: id for id, tag in enumerate(unique_tags)}
id2tag = {id: tag for tag, id in tag2id.items()}

tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-cased')

train_encodings = tokenizer(
    train_texts,
    is_split_into_words=True,
    return_offsets_mapping=True,
    padding=True,
    truncation=True)

validation_encodings = tokenizer(
    validation_texts,
    is_split_into_words=True,
    return_offsets_mapping=True,
    padding=True,
    truncation=True)


def encode_tags(tags, encodings):
    labels = [[tag2id[tag] for tag in doc] for doc in tags]
    encoded_labels = []
    for doc_labels, doc_offset in zip(labels, encodings.offset_mapping):
        # create an empty array of -100
        doc_enc_labels = np.ones(len(doc_offset), dtype=int) * -100
        arr_offset = np.array(doc_offset)

        # set labels whose first offset position is 0 and the second is not 0
        doc_enc_labels[
            (arr_offset[:, 0] == 0) & (arr_offset[:, 1] != 0)
        ] = doc_labels
        encoded_labels.append(doc_enc_labels.tolist())

    return encoded_labels


train_labels = encode_tags(train_labels, train_encodings)
validation_labels = encode_tags(validation_labels, validation_encodings)


# we don't want to pass this to the model
train_encodings.pop("offset_mapping")
validation_encodings.pop("offset_mapping")

train_dataset = tf.data.Dataset.from_tensor_slices((
    dict(train_encodings),
    train_labels
))

validation_dataset = tf.data.Dataset.from_tensor_slices((
    dict(validation_encodings),
    validation_labels
))

print('Saving datasets...')
tf.data.experimental.save(
    train_dataset,
    '/Users/nicholasmartin/Workspace/OS/dutch_neutrality_corpus'
    '/data/train_dataset')

tf.data.experimental.save(
    train_dataset,
    '/Users/nicholasmartin/Workspace/OS/dutch_neutrality_corpus'
    '/data/validation_dataset')

# print(train_dataset)

# model = \
#     TFDistilBertForTokenClassification.from_pretrained(
#         'distilbert-base-cased', num_labels=len(unique_tags))
