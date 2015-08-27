#!/bin/bash

tar -zxf mallet-2.0.7.tar.gz

if [ ! -f arxiv_word_weights.txt ]; then
   echo "Word weights file not present; building topic model out of arXiv data. This will only be done once."
   tar -zxf arxiv_ngrammed.tar.gz
   mallet-2.0.7/bin/mallet import-dir --token-regex "[\p{Alpha}_]{3,}" --input ngrammed/ --output arxiv.mallet --keep-sequence TRUE
   mallet-2.0.7/bin/mallet train-topics --input arxiv.mallet --output-topic-keys arxiv_topic_keys.txt --topic-word-weights-file arxiv_word_weights.txt --num-topics 150 --optimize-interval 15 --inferencer-filename arxiv.inferencer
   rm arxiv.mallet
   rm -rf ngrammed/
fi

echo "Processing BibTeX file"
cp bibtex_source/*.bib .
cat *.bib > all.txt
python allextract.py
python splitter.py
mkdir temp
mv file* temp/
for f in temp/file*
   do ./lemmatize -l lem-me-en.bin $f $f.lemmatized
done
tar -zxf arxiv_dataset.tar.gz 
mv temp/*.lemmatized arxiv_dataset/
python ngram.py
mkdir temp/temp2
mv arxiv_dataset/file* temp/temp2/
mallet-2.0.7/bin/mallet import-dir --token-regex "[\p{Alpha}_]{3,}" --input temp/temp2/ --output bibtex.mallet --keep-sequence TRUE
mallet-2.0.7/bin/mallet infer-topics --inferencer arxiv.inferencer --input bibtex.mallet --output-doc-topics bibtex_doc_topics.txt --doc-topics-threshold 0.05
python topicModelExtractor.py
mv all.txt ../docs/abstracts/bibtex.txt
echo "Cleaning up..."
rm -rf mallet-2.0.7
rm *.bib
rm all_processed.txt
rm -rf temp/
rm -rf arxiv_dataset/
rm bibtex.mallet
rm bibtex_doc_topics.txt
