# -*- coding: utf-8 -*-
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
import xlrd
import ujson
import jieba
from whoosh.qparser import QueryParser
from whoosh.index import open_dir
from whoosh.highlight import HtmlFormatter



base_path = 'D:/Users/wang_wei/Documents/GitHub/flask/examples/flaskr'
syn_path = base_path + '/syn.json'
cut_path = base_path + '/cut.json'
index_path = 'indexdir'
Filter = ['N','M','V','T','NR','NS','NT','NZ','VN']

def pre_process(word):
    wordx = []
    for i in word:
        wordx.append(i)
    syn_dict = {}
    with open(syn_path, 'r') as filehandle:
        syn_dict = ujson.loads(filehandle.read())

    for index,item in enumerate(wordx):
        for k,v in syn_dict.items():
            if item in v:
                wordx[index] = k

    return wordx

def build_index():
    data = xlrd.open_workbook('%s/searchengine/Travel-Normal.xls' % base_path)
    sheets = data.sheets()

    question = []
    answer = []
    for i in range(len(sheets)):
        for j in range(1, sheets[i].nrows):
            question.append(sheets[i].row_values(j)[0])
            answer.append(sheets[i].row_values(j)[3])
    
    schema = Schema(title=TEXT(stored=True),quesId=ID(stored=True))

    ix = open_dir("%s/searchengine/indexdir" % base_path)
    quesId = 0 

    writer = ix.writer()
    for i in question:
        words = jieba.cut_for_search(i)
        word = pre_process(words)
        writer.add_document(title=u' '.join(word),quesId = u'%s' % quesId)
        quesId += 1
    writer.commit()
    
def build():
    data = xlrd.open_workbook('%s/searchengine/Travel-Normal.xls' % base_path)
    sheets = data.sheets()

    question = []
    answer = []
    for i in range(len(sheets)):
        for j in range(1,sheets[i].nrows):
            question.append(sheets[i].row_values(j)[0])
            answer.append(sheets[i].row_values(j)[3])

    strq = ujson.dumps(question)
    stra = ujson.dumps(answer)
    fq = open('question.json', 'w')
    fq.write(strq)
    fq.close()

    fq = open('answer.json', 'w')
    fq.write(stra)
    fq.close()
    
def search_mess(mess, topN):
    data = xlrd.open_workbook('%s/searchengine/Travel-Normal.xls' % base_path)
    sheets = data.sheets()

    question = []
    for i in range(len(sheets)):
        for j in range(sheets[i].nrows):
            question.append(sheets[i].row_values(j)[0])
            
    ix = open_dir("%s/searchengine/indexdir" % base_path)
    parser = QueryParser('title', schema=ix.schema)
    words = pseg.cut(mess)
    word, tag = pre_process(words)
    
    query = []
    for idx,item in enumerate(tag):
        if item.upper() in Filter:
            query.append(word[idx])
    query = u' OR '.join(query)
    with ix.searcher() as searcher:
        query = parser.parse(query)
        results = searcher.search(query, limit=topN)
        hf = HtmlFormatter(tagname="font ", classname="match", termclass="t")

        results.formatter = hf
        
        result = []
        for item in results:
            #print item.highlights('title')
            result.append(question[int(item['quesId'])])
        return '=' + '='.join(result),len(result)

if __name__ == '__main__':
    build_index()
    ix = open_dir("%s/searchengine/indexdir" % base_path)
    parser = QueryParser('title', schema=ix.schema)
    with ix.searcher() as searcher:
            query = parser.parse(u'儿童')
            results = searcher.search(query, limit=5)
            print len(results)
            for i in results:
                print i['quesId']
