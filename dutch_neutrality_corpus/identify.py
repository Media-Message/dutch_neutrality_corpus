import re

# negative filter on revisions
INVALID_REVISION_REGEX = r'revert|undo|undid|robot'

# NPOV detector. Essentially looks for common pov-related words
#     pov, depov, npov, yespov, attributepov, rmpov, wpov, vpov, neutral
# with certain leading punctuation allowed
# Regex does not cover 'pov' ??

NPOV_REGEX = (r'([- wnv\/\\\:\{\(\[\"\+\'\.\|\_\)\#\=\;\~](rm)'
              r'?(attribute)?(yes)?(de)?n?pov)|([- n\/\\\:\{\('
              r'\[\"\+\'\.\|\_\)\#\;\~]neutral)')


def strip_tag_name(tag):
    idx = tag.rfind('}')
    if idx != -1:
        tag = tag[idx + 1:]
    return tag


# TODO: consider using DTO plus functions instead...
class RevisionComment():

    def __init__(self, element):
        self.revision_id = None
        self.timestamp = None
        self.comment = None
        self.extract_details(element=element)

    def extract_details(self, element):
        """  Store revision attributes """
        for child in list(element):

            child_tag = strip_tag_name(tag=child.tag)

            if child_tag == 'id':
                self.revision_id = child.text

            elif child_tag == 'comment':
                self.comment = child.text

            elif child_tag == 'timestamp':
                self.timestamp = child.text

    def is_complete(self):
        return not self.revision_id or not self.comment or not self.timestamp

    def is_admissible(self):

        if not self.comment:
            return False

        comment = self.comment.lower()

        if re.search(INVALID_REVISION_REGEX, comment):
            return False

        # TODO: create Dutch NPOV tags
        if re.search(NPOV_REGEX, comment):

            # TODO: remove redundancy later...
            # povere = poor
            # special case: "poverty", "impovershiment", etc
            if 'pover' in comment or 'povere' in comment:
                return False
            return True

        return False

    def asdict(self):
        return {
            'revision_id': self.revision_id,
            'timestamp': self.timestamp,
            'comment': self.comment
        }

    def __repr__(self):
        return f'{self.revision_id} {self.timestamp}: {self.comment}'


def apply_npov_identification(item_context):
    event, revision_element = item_context

    tag_name = strip_tag_name(tag=revision_element.tag)

    if not(event == 'start' and tag_name == 'revision'):
        return {}

    comment = RevisionComment(element=revision_element)

    if not comment.is_admissible():
        return {}

    return comment.asdict()
