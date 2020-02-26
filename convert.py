import os
import json
import re
import datetime
import argparse
import concurrent.futures
import logging
import time

from multiprocessing import Value

from lxml import etree

from somajo import SoMaJo
from someweta import ASPTagger

base = None
output = None

splitter = re.compile(r'[\n\r]+')

# tokenizer = SoMaJo('de_CMC')
tokenizer = None

model = "someweta/german_web_social_media_2018-12-21.model"
# tagger = ASPTagger()
# tagger.load(model)
# print('Tagger model loaded, beginning conversion')
tagger = None

def wrapjoin(lst, char='\n'):
    s = char.join([str(x) for x in lst])
    return char + s + char

def to_flist(lst):
    return wrapjoin(lst, '|')

def tokenize_tag(text):
    paragraphs = splitter.split(text)
    paragraphs = [p for p in paragraphs if p]

    sentences = tokenizer.tokenize_text(paragraphs)

    for sentence in sentences:
        sentence = [t.text for t in sentence]
        yield tagger.tag_sentence(sentence)

def add_sentences(element, sentences):
    global sentence_i

    for sentence in sentences:
        lines = [f'{word}\t{pos}' for word, pos in sentence]
        inner_text = wrapjoin(lines)

        with sentence_i.get_lock():
            sentence_element = etree.SubElement(element, 's', id=f's{sentence_i.value}')
            sentence_i.value += 1
        
        sentence_element.text = inner_text
        sentence_element.tail = '\n'

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

def process_file(path, file):
    global comment_i

    logger.debug(f'Processing file {os.path.join(path, file)}')

    with open(os.path.join(path, file), mode='r', encoding='utf-8-sig') as f:
        recipe = json.load(f, strict=False)

    if recipe['date']:
        d = datetime.datetime.strptime(recipe['date'], '%Y-%m-%d')
    else:
        d = None

    xml_recipe = etree.Element('recipe',
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

    logger.debug('\tTokenizing/tagging recipe')
    sentences = list(tokenize_tag(recipe['text']))

    add_sentences(xml_recipe, sentences)

    xml_comments = etree.Element('comments')
    xml_comments.tail = '\n'
    xml_comments.text = '\n'

    logger.debug('\tProcessing comments')
    for comment in recipe['comments']:

        if comment['date']:
            d = datetime.datetime.fromisoformat(comment['date'])
        else:
            d = None

        with comment_i.get_lock():
            xml_comment = etree.SubElement(xml_comments, 'comment',
                id = f'c{comment_i.value}',
                parent = recipe['id'],
                author = comment['author'],
                date = date(d),
                yearmonth = yearmonth(d),
                year = year(d),
                datetime_orig = comment['date']
            )
            comment_i.value += 1
        xml_comment.tail = '\n'
        xml_comment.text = '\n'

        sentences = tokenize_tag(comment['text'])

        add_sentences(xml_comment, sentences)

    
    recipe_file = file.split('.')[0] + '.vrt'
    recipe_path = path.replace(base, output + '/recipes/')
    os.makedirs(recipe_path, exist_ok=True)

    logger.debug(f'\tWriting recipe to {os.path.join(recipe_path, recipe_file)}')
    xml = etree.ElementTree(xml_recipe)
    xml.write(os.path.join(recipe_path, recipe_file), encoding='UTF-8', compression=False)

    if len(recipe['comments']) == 0:
        logger.debug('\tSkipping empty comments')
        return

    comments_file = file.split('.')[0] + '_comments.vrt'
    comments_path = path.replace(base, output + '/comments/')
    os.makedirs(comments_path, exist_ok=True)

    logger.debug(f'\tWriting comments to {os.path.join(comments_path, comments_file)}')
    xml = etree.ElementTree(xml_comments)
    xml.write(os.path.join(comments_path, comments_file), encoding='UTF-8', compression=False)


def init_worker(comment_counter, sentence_counter, worker_counter):

    global comment_i
    comment_i = comment_counter

    global sentence_i
    sentence_i = sentence_counter
    
    global logger
    logger = logging.getLogger(str(os.getpid()))
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hdl = logging.FileHandler(logger.name+'.log')
    hdl.setFormatter(fmt)
    hdl.setLevel(logging.DEBUG)
    logger.addHandler(hdl)

    logger.debug('Subprocess initializing')

    with worker_counter.get_lock():
        n = worker_counter.value
        worker_counter.value += 1
    
    logger.debug(f'Subprocess #{n} sleeping {n*25}s before continuing init')
    time.sleep(n*20)

    global tokenizer
    tokenizer = SoMaJo('de_CMC')
    logger.debug('Tokenizer loaded')

    global tagger
    tagger = ASPTagger()
    tagger.load(model)
    logger.debug('Tagger loaded')


def main():
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-o', default='output/vrt/', dest='outfolder',
        help='Sets the output folder.')
    argparser.add_argument('-i', dest='infolder', required=True,
        help='Sets the input folder.')
    argparser.add_argument('-t', type=int, default=1, dest='threads',
        help='Sets the number of parallell processes to use. Warning, very memory intensive!')
    
    args = argparser.parse_args()

    global base
    base = os.path.expanduser(args.infolder)

    global output
    output = os.path.expanduser(args.outfolder)

    paths = []

    for path, dirs, files in os.walk(base):
        for file in files:
            if file != 'index.dat':
                paths.append((path, file))

    workers = {}
    comment_i = Value('i')
    sentence_i = Value('i')
    worker_counter = Value('i')

    with concurrent.futures.ProcessPoolExecutor(max_workers = args.threads, initializer = init_worker,
        initargs = (comment_i, sentence_i, worker_counter)) as executor:
        for path, file in paths:
            workers[os.path.join(path, file)] = executor.submit(process_file, path, file)


if __name__ == "__main__":
    main()
