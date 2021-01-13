import unittest

from src.revision_retrieval import (
    get_wikipedia_revision_url
)


class TestRevisionRetrieval(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_wikipedia_revision_url(self):
        test_revision_id = 123456789
        expected_response = 'https://nl.wikipedia.org/wiki/?diff=123456789'
        response = get_wikipedia_revision_url(revision_id=test_revision_id)
        self.assertTrue(response == expected_response)
