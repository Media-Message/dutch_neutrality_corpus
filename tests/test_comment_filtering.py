import unittest

from dutch_neutrality_corpus.comment_filtering import (
    strip_tag_name
)


class TestRevision(unittest.TestCase):

    def setUp(self):
        pass

    def test_strip_tag_name(self):
        test_tag = 'this}that'
        expected_response = 'that'
        response = strip_tag_name(tag=test_tag)
        self.assertTrue(response == expected_response)
