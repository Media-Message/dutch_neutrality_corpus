# Dutch Wikipedia Neutrality Corpus
The Dutch Wikipedia Neutrality Corpus (DWNC) - a parallel corpus of biased and neutralized dutch sentence pairs. 

## Obtain Wikipedia Dump

Refer to the original code by [rpryzant](https://github.com/rpryzant/neutralizing-bias/tree/master/harvest). 

``` bash
wget https://dumps.wikimedia.org/nlwiki/20200901/nlwiki-20200901-stub-meta-history.xml.gz
gunzip nlwiki-20200901-stub-meta-history.xml.gz
export WIKI_DATA=nlwiki-20200901-stub-meta-history.xml
```

## Install Package

``` 
virtualenv venv
source venv/bin/activate
python -m pip install -e .
```

## Create Corpus

Identify NPOV revisions using comments from dump:

``` BASH
dutch_neutrality_corpus \
    --pipeline-name identify \
    --input-file data/nlwiki-20200901-stub-meta-history.xml \
    --output-file data/revision_comments.json \
    --n_revisions 100000
```

Crawl Wikipedia to obtain the revisions:

``` BASH
dutch_neutrality_corpus \
    --pipeline-name retrieve \
    --input-file data/revision_comments.json
```

Clean and prepare corpus:

``` BASH
dutch_neutrality_corpus \
    --pipeline-name prepare \
    --input-file data/revision_texts.json
```

Multiprocessing Mac
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

## Examples

3161315 2006-02-16T09:23:49Z: /* Sport */ wikify -pov
https://nl.wikipedia.org/wiki/?diff=3161315
https://nl.wikipedia.org/wiki/?diff=55462957
https://nl.wikipedia.org/wiki/?diff=9648885
https://nl.wikipedia.org/wiki/?diff=3161315

## Resources:

https://stackoverflow.com/questions/56888333how-can-i-parse-a-wikipedia-xml-dump-with-python
