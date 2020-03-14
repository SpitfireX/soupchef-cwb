#!/bin/bash

mkdir -p someweta && cd someweta
wget http://corpora.linguistik.uni-erlangen.de/someweta/german_web_social_media_2018-12-21.model
cd ..

mkdir -p treetagger && cd treetagger
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz
tar xzf tree-tagger-linux-3.2.2.tar.gz
tar xzf tagger-scripts.tar.gz
gunzip german.par.gz
mv german.par lib/german.par
rm tree-tagger-linux-3.2.2.tar.gz tagger-scripts.tar.gz
