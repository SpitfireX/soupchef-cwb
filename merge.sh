#!/bin/bash

python3 merge.py --gz -i output/vrt/recipes/ -o output/recipes.vrt.gz
python3 merge.py --gz --trim -i output/vrt/comments/ -o output/comments.vrt.gz
