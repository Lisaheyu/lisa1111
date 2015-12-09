#-*- coding: utf-8 -*-
import sys
import os
import copy
import ujson

FILE_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append('%s/../../Framework' % FILE_PATH)
synonyms_path = '%s/synonyms.json' % FILE_PATH
green_light_path = '%s/green_light.json' % FILE_PATH

import CtripCut as cut
#load base dict and create cut object
base_cut = cut.CnlpCut('base_out.dict', 'base.cache')
base_tag = cut.CnlpTag(base_cut)

#base cut
def cut_base(message):
    word = []
    tag = []
    segment = base_tag.cut(message)
    for item in segment:
        word.append(item.word)
        tag.append(item.flag)
    return word, tag


#base cut for get all words in sentence
def cut_base_for_search(message):
    word = []
    tag = []
    segment = base_tag.cut_for_search(message)
    for item in segment:
        word.append(item.word)
        tag.append(item.flag)
    return word, tag



def replace_mark(message_input):
    message = message_input
    if type(message) == str:
        message = message.replace('：', '点')
        message = message.replace(':', '点')
    elif type(message) == unicode:
        message = message.replace(u'：', u'点')
        message = message.replace(u':', u'点')
    return message

def preprocess(message):
    message_result = ''
    try:
        message_result = replace_mark(message)
    except:
        message_result = message
    word, tag =  cut_base(message_result)
    #print ' '.join(word)
    #print ' '.join(tag)
    add_preposition(word, tag, ['na','nb','nf'])
    synonyms_normalize(word)
    green_light(word, tag)
    catg = []
    for idx,item in enumerate(tag):
        if item in ['t', 'tz']:
            tag[idx] = 't'
        elif item in ['ns','na','nb','nc','nf','hs','npr','trz','dx','dz','jd']:
            tag[idx] = 'ns'
        else:
            pass

    #将相连的t合并
    word, tag = join_time_money(word, tag,['mm'])
    word, tag = join_time_money(word, tag,['t'])
    word, tag = join_time_money(word, tag,['md'])

    #print ' '.join(word)
    #print ' '.join(tag)
    catg = []
    for idx,item in enumerate(tag):
        if item in ['t','tj']:
            catg.append('t')
        elif item in ['ns','hb','h','m','mx','mmj','mdj','np','hx','fc','hf','trs','trl','hy']:
            catg.append(item)
        else:
            catg.append(word[idx])
    #print ' '.join(catg)
    word, catg = join_same_tag(word, catg, ['t'])
    word, catg = join_same_tag(word, catg, ['ns'])
    return catg, word


def synonyms_normalize(word):
    synonyms = {}
    with open(synonyms_path, 'r') as f:
        synonyms = ujson.loads(f.read())
    for index,item in enumerate(word):
        for k,v in synonyms.items():
            if item in v:
                word[index] = k


if __name__ == '__main__':
    with open('vacation_corpus.txt', 'r') as f:
        lines = f.read().split('\n')
    result = []
    for line in lines:
        catg, word = preprocess_travel(line)
        x = [word[idx]+' '+item for idx,item in enumerate(catg)]
        result.append('\n'.join(x))
    with open('vacation_corpus_preprocess.txt','w') as f:
        f.write(('\n'.join(result)).encode('utf-8'))

