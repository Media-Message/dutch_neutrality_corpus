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
		--input-file data/revision_html_full.json \
		--output-file data/revision_texts_full.json

prepare_doccano:
	dutch_neutrality_corpus \
		--pipeline-name prepare_doccano \
		--input-file data/revision_texts_full.json \
		--output-file data/revision_texts_doccano_full.json

retrieve_sample:
	dutch_neutrality_corpus \
		--pipeline-name retrieve \
		--input-file data/revision_comments.csv \
		--output-file data/revision_html.json \
	    --n_revisions 1000

diff_sample:
	dutch_neutrality_corpus \
		--pipeline-name diff \
		--input-file data/revision_html_sample.json \
		--output-file data/revision_texts_sample.json \
		--n_revisions 1000

prepare_doccano_sample:
	dutch_neutrality_corpus \
		--pipeline-name prepare_doccano \
		--input-file data/revision_texts_sample.json \
		--output-file data/revision_texts_doccano_sample.json

stream_log:
	 tail -f -n10 dwnc.log
