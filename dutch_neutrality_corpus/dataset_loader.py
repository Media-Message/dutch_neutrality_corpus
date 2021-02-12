# coding=utf-8
# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""TODO: Add a description here."""

from __future__ import absolute_import, division, print_function

import json
import os

import datasets


# TODO: Add BibTeX citation
# Find for instance the citation on arxiv or on the dataset repo/website
_CITATION = """1234"""

# TODO: Add description of the dataset here
# You can copy an official description
_DESCRIPTION = """\
This new dataset is designed to solve this great NLP task and is crafted with a lot of care.
"""

# TODO: Add a link to an official homepage for the dataset here
_HOMEPAGE = ""

# TODO: Add the licence for the dataset here if you can find it
_LICENSE = ""

SAMPLE_DATASET_FILEPATH = \
    ('/Users/nicholasmartin/Workspace/OS/'
     'dutch_neutrality_corpus/data/'
     'revision_texts_sample.json')

FULL_DATASET_FILEPATH = \
    ('/Users/nicholasmartin/Workspace/OS/'
     'dutch_neutrality_corpus/data/'
     'revision_texts_full.json')


class DutchNeutralityCorpusDataset(datasets.GeneratorBasedBuilder):
    """TODO: Short description of my dataset."""

    VERSION = datasets.Version("1.0.0")
    BUILDER_CONFIGS = [
        datasets.BuilderConfig(
            name="sample",
            version=VERSION,
            description="This is a sample of the dataset"),
        datasets.BuilderConfig(
            name="full",
            version=VERSION,
            description="This is the entire dataset"),
    ]

    def _info(self):
        features = datasets.Features(
            {
                "text": datasets.Value("string"),
                "tokens": datasets.Sequence(datasets.Value("string")),
                "class_labels": datasets.Sequence(
                    datasets.features.ClassLabel(
                        names=[
                            "SUBJ",
                            "NEUT"
                        ]
                    )
                )
            }
        )
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            supervised_keys=None,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""

        filepath = SAMPLE_DATASET_FILEPATH
        if self.config.name == "full":
            filepath = FULL_DATASET_FILEPATH

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={
                    "filepath": filepath
                }
            )
        ]

    def _generate_examples(self, filepath):
        """ Yields examples. """

        with open(filepath) as json_file:
            collection = json.load(json_file)

        for id_, row in enumerate(collection):

            yield id_, {
                'text': row['text'],
                'tokens': row['tokens'],
                'class_labels': row['class_labels']
            }
