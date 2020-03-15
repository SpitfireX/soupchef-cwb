#!/bin/bash

echo Creating directory structure
mkdir -p cwb/data/chefkoch cwb/data/chefkoch_comments cwb/registry/

echo encoding CHEFKOCH recipe corpus
cwb-encode -d cwb/data/chefkoch/ -R cwb/registry/chefkoch -f output/recipes.vrt.gz -c utf8 -xsB -S s:0+id -S text:0+title+id+url+author+date+yearmonth+year+rating+rating_int+category+category_orig+keywords+related+ingredients -P pos
echo making CHEFKOCH recipe corpus
cwb-make -r cwb/registry/ -M 2000 -V CHEFKOCH

echo encoding CHEFKOCH_COMMENTS corpus
cwb-encode -d cwb/data/chefkoch_comments/ -R cwb/registry/chefkoch_comments -f output/comments.vrt.gz -c utf8 -xsB -S s:0+id -S text:0+id+parent+author+date+yearmonth+year+datetime_orig -P pos
echo making CHEFKOCH_COMMENTS corpus
cwb-make -r cwb/registry/ -M 2000 -V CHEFKOCH_COMMENTS
