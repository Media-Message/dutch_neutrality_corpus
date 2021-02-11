from bs4 import BeautifulSoup

CATEGORIES_TO_FILTER = ['Categorieën', 'Categorie']
CATEGORY_REGEX = 'Categorie:*'


# TODO: "Twijfel aan de neutraliteit"
def extract_categories(html):
    soup = BeautifulSoup(html, features='html.parser')
    categories_html = soup.select("a[title*=Categorie]")
    categories = [a.text for a in categories_html
                  if a.text not in CATEGORIES_TO_FILTER]
    print(categories)
    return categories


def apply_category_filter(row):
    html = row['html_content']
    revision_categories = extract_categories(html=html)
    row['categories'] = revision_categories
    return row
