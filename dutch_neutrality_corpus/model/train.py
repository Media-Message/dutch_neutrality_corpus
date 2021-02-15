#!/usr/bin/env python3
import numpy as np
from transformers import AutoTokenizer
import datasets
from datasets import load_metric
from transformers import DataCollatorForTokenClassification
from transformers import (
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer)


class Builder():

    def __init__(self,
                 model_checkpoint='distilbert-base-uncased',
                 label_list=['SUBJ', 'NEUT'],
                 label_column='class_labels',
                 feature_column='tokens',
                 dataset_loading_script='dataset_loader.py',
                 metric='seqeval',
                 model_save_dir=None):
        self.model_checkpoint = model_checkpoint
        self.label_list = label_list
        self.label_column = label_column
        self.feature_column = feature_column
        self.dataset_loading_script = dataset_loading_script
        self.metric = metric
        self.model_save_dir = model_save_dir

        self.model_tokenizer = \
            self.load_tokenizer(model_checkpoint=model_checkpoint)
        self.model = \
            self.load_model(model_checkpoint=model_checkpoint)

    def load_dataset(self,
                     dataset_loading_script='dataset_loader.py',
                     dataset_type='sample'):
        return datasets.load_dataset(
            dataset_loading_script,
            dataset_type)

    def load_tokenizer(self, model_checkpoint):
        return AutoTokenizer.from_pretrained(model_checkpoint)

    def load_model(self, model_checkpoint):
        return AutoModelForTokenClassification.from_pretrained(
            self.model_checkpoint,
            num_labels=len(self.label_list))

    def encode_tokenizer(self, example):
        return self.model_tokenizer(
            example[self.feature_column],
            is_split_into_words=True,
            truncation=True,
            padding='max_length')

    def tokenize_and_align(self, examples, label_all_tokens=True):
        tokenized_text = \
            self.model_tokenizer(
                examples[self.feature_column],
                is_split_into_words=True,
                truncation=True)

        labels = []
        for i, label in enumerate(examples[self.label_column]):
            word_ids = tokenized_text.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx])
                else:
                    label_ids.append(
                        label[word_idx] if label_all_tokens else -100
                    )
                previous_word_idx = word_idx

            labels.append(label_ids)

        tokenized_text['labels'] = labels

        return tokenized_text

    def preprocess_dataset(self, dataset):
        return dataset.map(
            self.tokenize_and_align,
            batched=True)

    def train(self,
              dataset,
              batch_size=16):

        train_set = self.preprocess_dataset(
            dataset=dataset['train'])

        validation_set = self.preprocess_dataset(
            dataset=dataset['validation'])

        args = TrainingArguments(
            output_dir='experiments',
            evaluation_strategy='epoch',
            learning_rate=2e-5,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=1,
            weight_decay=0.01)

        data_collator = DataCollatorForTokenClassification(
            tokenizer=self.model_tokenizer)

        trainer = Trainer(
            model=self.model,
            args=args,
            train_dataset=train_set,
            eval_dataset=validation_set,
            data_collator=data_collator,
            tokenizer=self.model_tokenizer,
            compute_metrics=self.compute_metrics)

        trainer.train()

        return trainer

    def evaluate(self, trainer):
        trainer.evaluate()
        pass

    def test(self):
        pass

    def compute_metrics(self, prediction_and_labels):
        predictions, labels = prediction_and_labels
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (special tokens)
        true_predictions = [
            [self.label_list[p]
                for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [self.label_list[l]
                for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        # TODO: extract later...
        metric = load_metric("seqeval")

        results = metric.compute(
            predictions=true_predictions, references=true_labels)

        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

    def save_model(self, trainer):
        trainer.save_model(output_dir=self.model_save_dir)


if __name__ == '__main__':

    DATASET_LOADER_SCRIPT = \
        ('/Users/nicholasmartin/Workspace/OS/'
         'dutch_neutrality_corpus/dutch_neutrality_corpus/'
         'dataset_loader.py')

    builder = Builder(
        model_checkpoint='GroNLP/bert-base-dutch-cased')

    dataset = builder.load_dataset(
        dataset_loading_script=DATASET_LOADER_SCRIPT,
        dataset_type='sample')

    trainer = builder.train(dataset=dataset)

    builder.evaluate(trainer=trainer)

    builder.save_model(trainer=trainer)
