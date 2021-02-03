pip_install:
	python3 -m pip install -e .

identify_sample:
	dutch_neutrality_corpus \
		--pipeline-name identify \
		--input-file data/nlwiki-20200901-stub-meta-history.xml \
		--output-file data/revision_comments.csv \
		--n_revisions 100000

retrieve:
	dutch_neutrality_corpus \
		--pipeline-name retrieve \
		--input-file data/revision_comments.csv \
		--output-file data/revision_html.json

diff:
	dutch_neutrality_corpus \
		--pipeline-name diff \
		--input-file data/revision_html.json \
		--output-file data/revision_texts.json

prepare:
	dutch_neutrality_corpus \
		--pipeline-name prepare \
		--input-file data/revision_texts.json \
		--output-file data/neutrality_corpus.csv

retrieve_sample:
	dutch_neutrality_corpus \
		--pipeline-name retrieve \
		--input-file data/revision_comments.csv \
		--output-file data/revision_html.json \
	    --n_revisions 1000

diff_sample:
	dutch_neutrality_corpus \
		--pipeline-name diff \
		--input-file data/revision_html.json \
		--output-file data/revision_texts.json \
		--n_revisions 100

prepare_sample:
	dutch_neutrality_corpus \
		--pipeline-name prepare \
		--input-file data/revision_texts.json \
		--output-file data/neutrality_corpus.csv \
		--n_revisions 5

stream_log:
	 tail -f -n10 dwnc.log
