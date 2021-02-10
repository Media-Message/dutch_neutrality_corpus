#!/usr/bin/env python3

import logging
import requests


logging.basicConfig(
    level='INFO',
    format='%(asctime)s %(message)s',
    filename='dwnc.log')

# TODO: Parameterise language later...
DUTCH_WIKIPEDIA_REVISION_URL_TEMPLATE = \
    'https://nl.wikipedia.org/wiki/?diff={revision_id}'


def get_wikipedia_revision_url(revision_id):
    return DUTCH_WIKIPEDIA_REVISION_URL_TEMPLATE.format(
        revision_id=revision_id)


def query_url_with_backoff(url):
    session = requests.Session()
    response = session.get(url)
    return response.content.decode()


def retrieve_single_revision(row):
    revision_id = row['revision_id']
    logging.info(f'Processing revision_id={revision_id}')

    result = {}
    try:
        url = get_wikipedia_revision_url(revision_id=revision_id)
        html_content = query_url_with_backoff(url=url)
        result = {
            'revision_id': revision_id,
            'html_content': html_content
        }
    except Exception as e:
        # TODO: Ignore/filter out failed queries for now...
        logging.info(f'{e} revision_id={revision_id}')
        pass

    return result
