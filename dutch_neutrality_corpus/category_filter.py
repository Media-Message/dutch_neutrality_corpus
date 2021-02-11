from bs4 import BeautifulSoup


CATEGORY_SELECTOR = 'a[title*=Categorie]'
CATEGORIES_TO_IGNORE = ['Categorieën', 'Categorie']

# TODO: refine list as likely missing other topics...
# Ignore religious articles for now because of disputes
# over both the use of words as well as article facts.
# Fact checking is out of scope of this project.
PARTIAL_CATEGORIES_TO_FILTER = [
    'religiekritiek',
    'jezus',
    'mohammed',
    'jesus',
    'koran',
    'islam',
    'godsdienstfilosofie'
]


def is_wikipedia_category(text):
    return text.startswith('Wikipedia:')


def is_category_to_filter(text):
    contains_filtered_category = False
    for filter_category in PARTIAL_CATEGORIES_TO_FILTER:

        # Partial match in text
        if filter_category in text.lower():
            contains_filtered_category = True
            break

    return contains_filtered_category


def extract_categories(html):
    # TODO: "Twijfel aan de neutraliteit"
    soup = BeautifulSoup(html, features='html.parser')
    categories_html = soup.select(CATEGORY_SELECTOR)
    unique_categories = list(set([a.text for a in categories_html]))

    categories_to_keep = []
    wikipedia_categories = []
    categories_to_filter = []
    for text in unique_categories:

        if text in CATEGORIES_TO_IGNORE:
            continue

        elif is_wikipedia_category(text=text):
            wikipedia_categories.append(text)

        elif not is_category_to_filter(text=text):
            categories_to_keep.append(text)

        else:
            categories_to_filter.append(text)

    return (categories_to_keep,
            categories_to_filter,
            wikipedia_categories)


def apply_category_filter(row):
    html = row['html_content']

    categories_to_keep, categories_to_filter, wikpedia_article_tag = \
        extract_categories(html=html)

    revison_id = row['revision_id']

    if categories_to_filter:
        print(f'revision_id: {revison_id} '
              f'filter: {categories_to_filter} '
              f'keep: {categories_to_keep}')
        return {}

    row['categories'] = categories_to_keep
    row['internal_wikpedia_categories'] = wikpedia_article_tag

    return row
