import os
import json
import re
import datetime
import argparse

from lxml import etree

from somajo import SoMaJo
from someweta import ASPTagger

base = '/home/timm/projekte/chefkoch_dump/dump'
output = '/home/timm/projekte/wui_chefkoch_cwb/output/xml'

splitter = re.compile(r'[\n\r]+')

tokenizer = SoMaJo('de_CMC')

model = "someweta/german_web_social_media_2018-12-21.model"
tagger = ASPTagger()
tagger.load(model)
print('Tagger model loaded, beginning conversion')

comment_i = 0
sentence_i = 0

def wrapjoin(lst, char='\n'):
    s = char.join([str(x) for x in lst])
    return char + s + char

def to_flist(lst):
    return wrapjoin(lst, '|')

def tokenize_tag(text):
    paragraphs = splitter.split(text)

    sentences = tokenizer.tokenize_text(paragraphs)

    for sentence in sentences:
        sentence = [t.text for t in sentence]
        yield tagger.tag_sentence(sentence)

def add_sentences(element, sentences):
    global sentence_i
    for sentence in sentences:
        lines = [f'{word}\t{pos}' for word, pos in sentence]
        inner_text = wrapjoin(lines)
        sentence_element = etree.SubElement(element, 's', id=f's{sentence_i}')
        sentence_element.text = inner_text
        sentence_element.tail = '\n'
        sentence_i += 1

def date(d):
    if d:
        return d.strftime('%Y-%m-%d')
    else:
        return '0000-00-00'

def yearmonth(d):
    if d:
        return d.strftime('%Y-%m')
    else:
        return '0000-00'

def year(d):
    if d:
        return d.strftime('%Y')
    else:
        return '0000'

paths = []

for path, dirs, files in os.walk(base):
    for file in files:
        if file != 'index.dat':
            paths.append((path, file))

for path, file in paths:

    with open(os.path.join(path, file), mode='r', encoding='utf-8-sig') as f:
        recipe = json.load(f, strict=False)

    xml_root = etree.Element('entry')
    xml_root.tail = '\n'
    xml_root.text = '\n'

    if recipe['date']:
        d = datetime.datetime.strptime(recipe['date'], '%Y-%m-%d')
    else:
        d = None

    xml_recipe = etree.SubElement(xml_root, 'recipe',
        title = recipe['title'],
        id = recipe['id'],
        url = recipe['url'],
        author = recipe['author'],
        date = date(d),
        yearmonth = yearmonth(d),
        year = year(d),
        rating = str(recipe['rating'].get('value')),
        category = recipe['category'],
        keywords = to_flist(recipe['keywords']),
        related = to_flist(recipe['related']),
        ingredients = to_flist([x['name'] for x in recipe['ingredients']])
    )
    xml_recipe.tail = '\n'
    xml_recipe.text = '\n'

    sentences = list(tokenize_tag(recipe['text']))

    add_sentences(xml_recipe, sentences)

    for comment in recipe['comments']:

        if comment['date']:
            d = datetime.datetime.fromisoformat(comment['date'])
        else:
            d = None

        xml_comment = etree.SubElement(xml_root, 'comment',
            id = f'c{comment_i}',
            parent = recipe['id'],
            author = comment['author'],
            date = date(d),
            yearmonth = yearmonth(d),
            year = year(d),
            datetime_orig = comment['date']
        )
        xml_comment.tail = '\n'
        xml_comment.text = '\n'

        sentences = tokenize_tag(comment['text'])

        add_sentences(xml_comment, sentences)

        comment_i += 1
    
    newfile = file.split('.')[0] + '.vrt'
    newpath = path.replace(base, output)

    os.makedirs(newpath, exist_ok=True)

    xml = etree.ElementTree(xml_root)
    xml.write(os.path.join(newpath, newfile), encoding='unicode', compression=False)
