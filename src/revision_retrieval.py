import sys
import re
import logging
import string
from urllib.request import urlopen

from bs4 import BeautifulSoup

# TODO: refactor...


# TODO: Parameterise language later...
DUTCH_WIKIPEDIA_REVISION_URL_TEMPLATE = \
    'https://nl.wikipedia.org/wiki/?diff={revision_id}'


def get_wikipedia_revision_url(revision_id):
    return DUTCH_WIKIPEDIA_REVISION_URL_TEMPLATE.format(
        revision_id=revision_id)


def html2diff(html):
    prev_changed, next_changed = [], []
    prev_deleted, next_added = [], []

    soup = BeautifulSoup(html, features='html.parser')

    nodes = soup.find_all(class_=re.compile(
        r'(diff-deletedline)|(diff-addedline)|(diff-empty)'))
    div_p = re.compile(r'<div.*?>(.*)</div>', re.DOTALL)

    for i in range(0, len(nodes), 2):

        # skip straddeling cases
        if i + 1 >= len(nodes):
            continue

        node_prev = nodes[i]
        node_next = nodes[i + 1]

        # seperate revisions into chunks that were modified,
        # chunks that were purely deleted and chunks that were purely added
        if not node_prev.div and not node_next.div:
            continue

        elif not node_prev.div:
            next_match = re.match(
                div_p,
                node_next.div.prettify(formatter=None))

            if next_match:
                next_added.append(next_match.group(1).strip())

        elif not node_next.div:
            prev_match = re.match(
                div_p,
                node_prev.div.prettify(formatter=None))

            if prev_match:
                prev_deleted.append(prev_match.group(1).strip())

        else:
            prev_match = re.match(
                div_p, node_prev.div.prettify(formatter=None))
            next_match = re.match(
                div_p, node_next.div.prettify(formatter=None))

            if prev_match and next_match:
                prev_changed.append(prev_match.group(1).strip())
                next_changed.append(next_match.group(1).strip())

    return prev_changed, next_changed, prev_deleted, next_added


def url2diff(url):
    try:
        response = urlopen(url)
        html = response.read()
        return html2diff(html)
    except Exception as e:
        print(e, file=sys.stderr)
        return [], [], [], []


def wiki_text_clean(text):
    text = ''.join([x for x in text if x in string.printable])
    text = text.replace('\n', ' ').replace('\t', ' ')
    return text


def retrieve_single_revision(row):
    revision_id = row['revision_id']

    logging.info(f'Processing revision_id={revision_id}')

    url = get_wikipedia_revision_url(revision_id=revision_id)

    prior_, post_, prior_deleted, post_added = url2diff(url=url)

    # TODO: add later...
    # if len(prevs_) != len(nexts_):
    #     logging.info('ERROR: corpus sizes not equal!')
    #     continue

    prior, post = [], []

    for prior_text, post_text in zip(prior_, post_):
        prior.append(wiki_text_clean(prior_text))
        post.append(wiki_text_clean(post_text))

    prior_deleted = \
        [wiki_text_clean(prior_text) for prior_text in (
            prior_deleted or ['no_deleted_chunks'])]
    post_added = \
        [wiki_text_clean(post_text) for post_text in (
            post_added or ['no_added_chunks'])]

    return {
        'revision_id': revision_id,
        'prior': prior,
        'post': post,
        'prior_deleted': prior_deleted,
        'post_added': post_added
    }
