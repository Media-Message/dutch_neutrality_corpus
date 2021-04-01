

def is_only_numbers(text):
    return ''.join(text).isdecimal()


def is_length_one(tokens):
    return len(tokens) == 1


def is_image_tag(text):
    image_tags = ['png', 'jpeg', 'jpg']
    return text in image_tags


def apply_content_filter(row):
    text, tokens = row['text'], row['tokens']

    # TODO: consider at least two words...
    filter_example = \
        is_only_numbers(text) or \
        is_length_one(tokens) or \
        is_image_tag(text)

    if filter_example:
        return {}

    return row
