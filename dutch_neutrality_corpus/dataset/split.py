import logging

import numpy as np
from sklearn.model_selection import train_test_split


class TrainValidationTestSplitStage():

    def __init__(self,
                 labels_column,
                 train_set_ratio=.7,
                 validation_set_ratio=.15,
                 test_set_ratio=.15):
        self.labels_column = labels_column
        self.train_set_ratio = train_set_ratio
        self.validation_set_ratio = validation_set_ratio
        self.test_set_ratio = test_set_ratio
        self.check_ratio_sum(
            train_set_ratio,
            validation_set_ratio,
            test_set_ratio)

    def check_ratio_sum(self,
                        train_set_ratio,
                        validation_set_ratio,
                        test_set_ratio):
        ratio_sum = np.sum([train_set_ratio,
                            validation_set_ratio,
                            test_set_ratio])
        assert ratio_sum == 1, 'combined ratios must not sum to 1.'

    def remove_key_from_dict(self, dictionary, key):
        return {k: v for k, v in dictionary.items() if k != key}

    def get_features(self, collection, label_field):
        # All fields except labels
        return \
            [self.remove_key_from_dict(d, key=self.labels_column)
             for d in collection]

    def get_labels(self, collection, label_field):
        return [d[label_field] for d in collection]

    def get_combined_validation_and_test_set_ratio(self, train_ratio):
        return 1 - train_ratio

    def get_relative_validation_and_test_set_ratio(self,
                                                   test_ratio,
                                                   validation_ratio):
        return test_ratio/(test_ratio + validation_ratio)

    def merge_list_of_dicts(self, list_a, list_b):
        return [
            {
                **a,
                **{self.labels_column: b}
            } for a, b in zip(list_a, list_b)
        ]

    def apply(self, collection):
        logging.info('Beginning dataset splitting...')

        features = self.get_features(
            collection=collection,
            label_field=self.labels_column)

        labels = self.get_labels(
            collection=collection,
            label_field=self.labels_column)

        combined_test_set_size = \
            self.get_combined_validation_and_test_set_ratio(
                train_ratio=self.train_set_ratio)

        relative_validation_test_set_size = \
            self.get_relative_validation_and_test_set_ratio(
                validation_ratio=self.validation_set_ratio,
                test_ratio=self.test_set_ratio)

        x_train, x_other, y_train, y_other = \
            train_test_split(
                features,
                labels,
                test_size=combined_test_set_size)

        x_validation, x_test, y_validation, y_test = \
            train_test_split(
                x_other,
                y_other,
                test_size=relative_validation_test_set_size)

        logging.info('Completed dataset splitting...')

        train_set = self.merge_list_of_dicts(x_train, y_train)
        validation_set = self.merge_list_of_dicts(x_validation, y_validation)
        test_set = self.merge_list_of_dicts(x_test, y_test)

        return {
            'train.json': train_set,
            'validation.json': validation_set,
            'test.json': test_set
        }
