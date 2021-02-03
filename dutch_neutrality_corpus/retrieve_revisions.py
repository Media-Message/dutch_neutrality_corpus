#!/usr/bin/env python3

import logging
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(
    level='INFO',
    format='%(asctime)s %(message)s',
    filename='dwnc.log')

RETRIES = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[502, 503, 504]
)

# TODO: Parameterise language later...
DUTCH_WIKIPEDIA_REVISION_URL_TEMPLATE = \
    'https://nl.wikipedia.org/wiki/?diff={revision_id}'


def get_wikipedia_revision_url(revision_id):
    return DUTCH_WIKIPEDIA_REVISION_URL_TEMPLATE.format(
        revision_id=revision_id)


def query_url_with_backoff(url):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=RETRIES))
    response = session.get(url)
    return response.content.decode()


def retrieve_single_revision(row):

    revision_id = row['revision_id']
    logging.info(f'Processing revision_id={revision_id}')

    result = None
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
