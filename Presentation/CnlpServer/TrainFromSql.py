#-*- coding: utf-8 -*-
import redis
import ujson
import sys
import os
import time

FILE_PATH = os.path.split(os.path.realpath(__file__))[0]
CONF_PATH = '%s/../../Config/' % FILE_PATH

sys.path.append('%s/../../Logic/PreProcess' % FILE_PATH)
sys.path.append('%s/../../DataAccess' % FILE_PATH)
sys.path.append('%s/../../Entity' % FILE_PATH)

import PreProcess as PProc
import ConnectMsSql as CMS
import DataStruct as DS

from whoosh.index import create_in
from whoosh.fields import *

STAY_TAG = ['N','M','V','T','NR','NS','NT','NZ','D','S','A','F','VN','L']

def updata_redis(Knowledge, Word, worddir, RedisDBid):
    r = redis.StrictRedis(host='localhost', port=6379, db=RedisDBid)
    r.flushdb()
    Question = []
    Answer = []
    for KID,item in Knowledge.items():
        for question in item[0]:
            if int(question.IsNorm) == 1:
                Question.append(question)
    for KID,item in Knowledge.items():
        for ChannelID,item in item[1].items():
            Answer.append(item)
    #更新问题
    for item in Question:
        key = 'Q%s' % item.QuestionID
        r.hset(key,'KnowledgeID',item.KnowledgeID)
        r.hset(key,'Qitem',item.Question)
    #更新答案
    for item in Answer:
        key = 'A%s' % item.AnswerID
        r.hset(key,'KnowledgeID',item.KnowledgeID)
        r.hset(key,'Aitem',item.Answer)
    #更新knowledge关联的问题列表和答案字典
    for KnowledgeID,value in Knowledge.items():
        qkey = 'Qlist%s' % KnowledgeID
        for question in value[0]:
            r.rpush(qkey,question.QuestionID)
        akey = 'Alist%s' % KnowledgeID
        for channelid,answer in value[1].items():
            r.hset(akey,channelid,answer.AnswerID)
    #更新同义词典
    word2dim = []
    for item in Word:
        if item.Synonyms != '':
            WordName = item.WordName
            Synonyms = item.Synonyms
            wordlist = []
            wordlist.append(WordName)
            wordlist.extend(Synonyms.split('|'))
            word2dim.append(wordlist)
    wordresult = []
    for item in word2dim:
        ambiguity = set()
        for idx,row in enumerate(wordresult):
            for i in item:
                if i in row:
                    ambiguity.add(idx)
        if len(ambiguity) == 0:
            wordresult.append(item)
        elif len(ambiguity) == 1:
            for i in ambiguity:
                wordresult[i].extend(item)
        else:
            pass
    worddict = {}
    for item in wordresult:
        #print type(item[0])
        worddict[item[0]] = item[1:]
    resultstr = ujson.dumps(worddict)
    with open(worddir,'w') as f:
        f.write(resultstr)

'''
updata aiml for pyaiml
'''
def SegProcess(word, tag):
    cutstr = ''
    wordx = []
    tagx = []
    with open(CUT_PATH, 'r') as f:
        cutstr = f.read()
    cut = ujson.loads(cutstr)
    for idx,item in enumerate(word):
        if item not in cut:
            wordx.append(item)
            tagx.append(tag[idx].upper())

    syn_dict = {}
    with open(SYN_PATH, 'r') as filehandle:
        syn_dict = ujson.loads(filehandle.read())

    for index,item in enumerate(wordx):
        for k,v in syn_dict.items():
            if item in v:
                wordx[index] = k

    return wordx, tagx

def RepalceQueMark(catg, item):
    result = []
    numberofmark = len(item)
    IdxOfMark = 0
    for i in catg:
        if i == '?':
            if item[IdxOfMark] == '1':
                result.append('>')
            elif item[IdxOfMark] == '0':
                result.append('<')
            IdxOfMark += 1
        else:
            result.append(i)

    return result

def ReStar(item):
    result = []
    flag = True
    for i in item:
        if i == '*' and flag is True:
            result.append(i)
            flag = False
        elif i != '*':
            result.append(i)
            flag = True
    return result

def PreProcesscatg(catg):
    if len(catg) == 0 or (len(catg) == 1 and catg[0] == '*'):
        return []
    lenOfCatg = len(catg)
    i = 0
    j = 0
    while(i < lenOfCatg):
        if catg[i] != '*':
            break
        i += 1

    while(j >= 0):
        if catg[j] != '*':
            break
        j -= 1
    #print i,j
    if j+1 >= 0:
        catg = catg[i:]
    else:
        catg = catg[i:j+1]

    if catg[0] == '*':
        catg[0] = '?'
    else:
        catg.insert(0,'?')
    if catg[-1] == '*':
        catg[-1] = '?'
    else:
        catg.append('?')
    return catg

def QuestionGet(word, tag):
    if len(word) == 0:
        return []
    result = []
    catg = []
    for idx,item in enumerate(word):
        if item == '=':
            catg.append('?')
        elif tag[idx].upper() in STAY_TAG:
            catg.append(item)
        else:
            catg.append('*')
    #print ' '.join(catg)
    catg = PreProcesscatg(catg)
    #print catg
    mid = []
    midbit = []
    NumberOf0 = 0
    for item in catg:
        if item == '?':
            NumberOf0 += 1
    for idx in range(0, 2**NumberOf0):
        midbit.append(('{0:0%sb}' % NumberOf0).format(idx))

    for idx,item in enumerate(midbit):
        mid.append(RepalceQueMark(catg,item))

    for idx,item in enumerate(mid):
        pmid = []
        for idx1,item1 in enumerate(mid[idx]):
            if item1 == '>':
                pmid.append('*')
            elif item1 != '<':
                pmid.append(item1)
        mid[idx] = pmid

    for idx,item in enumerate(mid):
        mid[idx] = ReStar(mid[idx])

    return mid

def QuestionGet_chat(word, tag):
    if len(word) == 0:
        return []
    result = []
    catg = []
    for idx,item in enumerate(word):
        if item == '=':
            catg.append('?')
        elif tag[idx].upper() not in []:
            catg.append(item)
        else:
            catg.append('*')
    #print ' '.join(catg)
    catg = PreProcesscatg(catg)
    #print catg
    mid = []
    midbit = []
    NumberOf0 = 0
    for item in catg:
        if item == '?':
            NumberOf0 += 1
    for idx in range(0, 2**NumberOf0):
        midbit.append(('{0:0%sb}' % NumberOf0).format(idx))

    for idx,item in enumerate(midbit):
        mid.append(RepalceQueMark(catg,item))

    for idx,item in enumerate(mid):
        pmid = []
        for idx1,item1 in enumerate(mid[idx]):
            if item1 == '>':
                pmid.append('*')
            elif item1 != '<':
                pmid.append(item1)
        mid[idx] = pmid

    for idx,item in enumerate(mid):
        mid[idx] = ReStar(mid[idx])

    return mid

def ProcessRow(row):
    result = []
    for question in row:
        filter = [u'，',u'？',u'。',u'；',u'！',u'“',u'”',u'’',u'‘',u',',u'.',u'!','?']
        for i in filter:
            question = question.replace(i, '')

        lenOfQ = len(question)
        if lenOfQ == 0:
            continue
        listOfWildcard = []
        for i in range(lenOfQ):
            if question[i] == '=':
                listOfWildcard.append(i)

        word,tag = PProc.withtag_cut(question)

        for idx in listOfWildcard:
            imid = 0
            for idxOfword,item in enumerate(word):
                if imid == idx:
                    word.insert(idxOfword, u'=')
                    tag.insert(idxOfword, 'wc')
                    break
                imid += len(item)

        word, tag = PProc.wordtag_process(word, tag)
        #print ' '.join(word)
        result += QuestionGet(word, tag)

    return result

def ProcessRow_chat(row):
    result = []
    for question in row:
        filter = [u'，',u'？',u'。',u'；',u'！',u'“',u'”',u'’',u'‘',u',',u'.',u'!','?']
        for i in filter:
            question = question.replace(i, '')

        lenOfQ = len(question)
        if lenOfQ == 0:
            continue
        listOfWildcard = []
        for i in range(lenOfQ):
            if question[i] == '=':
                listOfWildcard.append(i)

        word,tag = PProc.withtag_cut(question)

        for idx in listOfWildcard:
            imid = 0
            for idxOfword,item in enumerate(word):
                if imid == idx:
                    word.insert(idxOfword, u'=')
                    tag.insert(idxOfword, 'wc')
                    break
                imid += len(item)

        word, tag = PProc.wordtag_process(word, tag)
        #print ' '.join(word)
        result += QuestionGet_chat(word, tag)

    return result

def WriteAiml(knowledge, stringS, stringT, ID, fw):
    #print ID
    questionList = []
    for item in knowledge:
        questionList.append(item.Question)

    result = ProcessRow(questionList)
    stringTx = stringT.replace('KEY', (u'KNOWLEDGE %s' % ID).encode('utf-8'))
    stringTx = stringTx.replace('VALUE', 'match-normal|%s' % ID)
    fw.write(stringTx)

    for item in result: 
        stringSx = stringS.replace('KEY', ' '.join(item).encode('utf-8'))
        stringSx = stringSx.replace('VALUE', (u'KNOWLEDGE %s' % ID).encode('utf-8'))
        fw.write(stringSx)

def WriteAiml_what(knowledge, string_what, ID, fw_match):
    if len(knowledge) < 2:
        return
    key = knowledge[1].Question
    keyList, tag = PProc.withtag_cut(key)
    PProc.syn_wordlist(keyList)
    stringx = string_what.replace('KNOW', (u'KNOWLEDGE %s' % ID).encode('utf-8'))
    stringx = stringx.replace('KEY', ' '.join(keyList).encode('utf-8'))
    stringx = stringx.replace('VALUE', (u'match-what|%s' % ID).encode('utf-8'))
    fw_match.write(stringx)

def WriteAiml_how(knowledge,string_how,ID, fw_match):
    if len(knowledge) < 2:
        return
    question = []
    for item in knowledge:
        question.append(item.Question)

    parm = question[1]
    key = parm.split('>')[0]
    verb = parm.split('>')[1]
    keyList = PProc.withtag_cut(key)[0]
    PProc.syn_wordlist(keyList)
    verb = PProc.syn_word(verb)
    if '0' not in keyList:
        stringx = string_how.replace('KNOW', (u'KNOWLEDGE %s' % ID).encode('utf-8'))
        stringx = stringx.replace('KEY', ' '.join(keyList).encode('utf-8'))
        stringx = stringx.replace('VERB', verb.encode('utf-8'))
        stringx = stringx.replace('VALUE', (u'match-what|%s' %ID).encode('utf-8'))
        fw_match.write(stringx)
    else:
        keyList[keyList.index('0')] = '*'
        stringx = string_how.replace('KNOW', (u'KNOWLEDGE %s' % ID).encode('utf-8'))
        stringx = stringx.replace('KEY', ' '.join(keyList).encode('utf-8'))
        stringx = stringx.replace('VERB', verb.encode('utf-8'))
        stringx = stringx.replace('VALUE', (u'match-what|%s' % ID).encode('utf-8'))
        fw_match.write(stringx)
        keyList.remove('*')
        stringx = string_how.replace('KNOW', (u'KNOWLEDGE %s' % ID).encode('utf-8'))
        stringx = stringx.replace('KEY', ' '.join(keyList).encode('utf-8'))
        stringx = stringx.replace('VERB', verb.encode('utf-8'))
        stringx = stringx.replace('VALUE', (u'match-what|%s' % ID))
        fw_match.write(stringx)

def WriteAiml_chat(chat,stringS,stringT,fw_chat):
    pattern = chat.Question.split('>')
    question = pattern[0].split('|')
    that = ''
    if len(pattern) > 1:
        that = pattern[1]
    else:
        that = None
    answer = chat.Answer.split('|')
    ID = chat.DlgID

    result = ProcessRow_chat(question)
    answerstr = '<random>\n'
    for item in answer:
        answerstr += ('<li>chat|%s</li>\n' % item)
    answerstr += '</random>'

    stringTx = stringT.replace('KEY', (u'CHAT %s' % ID).encode('utf-8'))
    stringTx = stringTx.replace('VALUE', answerstr.encode('utf-8'))
    fw_chat.write(stringTx)

    for item in result: 
        stringSx = stringS.replace('KEY', ' '.join(item).encode('utf-8'))
        stringSx = stringSx.replace('VALUE', (u'CHAT %s' % ID).encode('utf-8'))
        if that != None:
            position = stringSx.find('</pattern>')
            stringSx = stringSx[0: position+len('</pattern>')] + '\n<that>CHAT|%s</that>' \
                       % that.encode('utf-8') + stringSx[position+len('</pattern>'):]
        fw_chat.write(stringSx)

def updata_aiml(Knowledge, Chat, aimlPath):
    frS = open(('%s/srai.mod' % aimlPath),'rb')
    frT = open(('%s/template.mod' % aimlPath),'rb')

    fr_what = open(('%s/what.mod' % aimlPath),'rb')
    fr_how = open(('%s/how.mod' % aimlPath),'rb')
    stringS = frS.read().decode('utf-8').encode('utf-8')
    stringT = frT.read().decode('utf-8').encode('utf-8')

    string_what = fr_what.read().decode('utf-8').encode('utf-8')
    string_how = fr_how.read().decode('utf-8').encode('utf-8')

    NORMAL_AIML_PATH = '%s/travel_normal.aiml' % aimlPath
    MATCH_AIML_PATH = '%s/travel_match.aiml' % aimlPath
    CHAT_AIML_PATH = '%s/client.aiml' % aimlPath

    fwx = open(NORMAL_AIML_PATH, 'wb')
    fwx_match = open(MATCH_AIML_PATH, 'wb')
    fwx_chat = open(CHAT_AIML_PATH, 'wb')

    fwx.write('<aiml>\n')
    fwx_match.write('<aiml>\n')
    fwx_chat.write('<aiml>\n')
    fwx.close()
    fwx_match.close()
    fwx_chat.close()
    fw = open(NORMAL_AIML_PATH, 'ab')
    fw_match = open(MATCH_AIML_PATH, 'ab')
    fw_chat = open(CHAT_AIML_PATH, 'ab')

    for KnowledgeID,item in Knowledge.items():
        NormQ = item[0][0]
        for question in item[0]:
            if int(question.IsNorm) == 1:
                NormQ = question

        if NormQ.ModelID == 1:
            WriteAiml_what(item[0],string_what,KnowledgeID, fw_match)
        elif NormQ.ModelID == 2:
            WriteAiml_how(item[0],string_how,KnowledgeID, fw_match)
        else:
            WriteAiml(item[0],stringS,stringT,KnowledgeID, fw)

    for chatItem in Chat:
        WriteAiml_chat(chatItem,stringS,stringT,fw_chat)

    fw.write('\n</aiml>')
    fw_match.write('\n</aiml>')
    fw_chat.write('<category>\n<pattern>*</pattern>\n<template>\n<random>\n'\
                  '<li>none|这个回答起来比较困难哦。</li>\n<li>none|让我们换个话题吧。</li>\n'\
                  '<li>none|嗯不好说哦</li>\n<li>none|这个我不知道怎么答哦。</li>\n'\
                  '</random>\n</template>\n</category>\n</aiml>')
    frS.close()
    frT.close()
    fr_what.close()
    fr_how.close()
    fw.close()
    fw_match.close()
    fw_chat.close()

'''
updata SearchEngine
'''
def updata_searchengine(Knowledge,SeIndexDir):
    #remove old index
    os.system('rm -rf %s' % SeIndexDir)
    os.system('mkdir %s' % SeIndexDir)

    QuestionNorm = []
    for KID,item in Knowledge.items():
        for question in item[0]:
            if int(question.IsNorm) == 1:
                QuestionNorm.append(question)

    question = []
    for item in QuestionNorm:
        mid = {}
        mid['question'] = item.Question
        mid['questionID'] = item.QuestionID
        question.append(mid)

    schema = Schema(title=TEXT(stored=True),quesId=ID(stored=True))
    ix = create_in(SeIndexDir, schema)

    writer = ix.writer()
    for i in question:
        word = PProc.cut_for_search(i['question'])
        PProc.syn_wordlist(word)
        writer.add_document(title=u' '.join(word),quesId = u'%s' % i['questionID'])
    writer.commit()

def train(pathdict):
    try:
        ms = CMS.MSSQL(host="Onlinehelp.db.sh.ctriptravel.com,55944",\
                       user='uapp_SyncComMsg',\
                       pwd='WNv/R5j3ppAIKOrCXR94=',db="LiveChatDB")
        sql = 'SELECT [KnowledgeID], [DepartmentID] FROM [LiveChatDB].'\
              '[dbo].[CRobot_Knowledge](nolock)'
        midKnowledge = ms.ExecQuery(sql)
        Knowledge = []
        for item in midKnowledge:
            Knowledge.append(DS.Knowledge(item))

        sql = 'SELECT [WordName], [Synonyms] from [LiveChatDB].[dbo].'\
              '[CRobot_Word](nolock)'
        midSymWord = ms.ExecQuery(sql)
        SymWord = []
        for item in midSymWord:
            SymWord.append(DS.Word(item))

        sql = 'SELECT CommonDlgID, Question, cast(Answer as text) as Answer '\
              'from [LiveChatDB].[dbo].[CRobot_CommonDlg](nolock)'
        midChat = ms.ExecQuery(sql)
        Chat = []
        for item in midChat:
            Chat.append(DS.Chat(item))

        sql = 'SELECT QuestionID, KnowledgeID, Question, IsNorm, ModelID '\
              'from [LiveChatDB].[dbo].[CRobot_Question](nolock)'
        Question = []
        reslist = ms.ExecQuery(sql)
        for item in reslist:
            Question.append(DS.Question(item))

        sql = 'SELECT AnswerID, KnowledgeID, cast(Answer as text) as Answer,'\
              'ChannelID from [LiveChatDB].[dbo].[CRobot_Answer](nolock) '
        reslist = ms.ExecQuery(sql)
        Answer = []
        for item in reslist:
            Answer.append(DS.Answer(item))

        KnowledgeDict = {}
        for Kitem in Knowledge:
            param = Kitem.KnowledgeID

            qlist = []
            for item in Question:
                if item.KnowledgeID == param:
                    qlist.append(item)

            alist = []
            adict = {}
            for item in Answer:
                if item.KnowledgeID == param:
                    alist.append(item)

            for item in alist:
                adict[item.ChannelID] = item

            KnowledgeDict[param] = []
            KnowledgeDict[param].append(qlist)
            KnowledgeDict[param].append(adict)
            KnowledgeDict[param].append(Kitem.DepartmentID)

        updata_redis(KnowledgeDict, SymWord, pathdict['synPath'],pathdict['redisDbID'])
        updata_aiml(KnowledgeDict, Chat, pathdict['aimlPath'])
        updata_searchengine(KnowledgeDict, pathdict['seIndexDir'])
    except:
        pass

if __name__ == '__main__':
    configDB = 3
    processerNum = 4#uwsgi processer number
    timeSleep = 600
    '''
    r = redis.StrictRedis(host='localhost', port=6379, db=configDB)
    pathdict = {}
    pathdict['synPath'] = r.get('synPath')
    pathdict['aimlPath'] = r.get('aimlPath')
    pathdict['redisDbID'] = r.get('redisDbID')
    pathdict['seIndexDir'] = r.get('seIndexDir')
    print  pathdict['aimlPath']
    train(pathdict)
    #r.set('leaveProcessTimes', processerNum)
    #r.set('resetStatusNum', processerNum)

    '''
    while(True):
        r = redis.StrictRedis(host='localhost', port=6379, db=configDB)
        leaveProcessTimes = r.get('leaveProcessTimes')
        resetStatusNum = r.get('resetStatusNum')
        if int(leaveProcessTimes) > 0 or '0' != resetStatusNum:
            time.sleep(timeSleep)
            continue
        pathdict = {}
        pathdict['synPath'] = r.get('synPath')
        pathdict['aimlPath'] = r.get('aimlPath')
        pathdict['redisDbID'] = r.get('redisDbID')
        pathdict['seIndexDir'] = r.get('seIndexDir')
        train(pathdict)
        r.set('leaveProcessTimes', processerNum)
        r.set('resetStatusNum', processerNum)
        time.sleep(timeSleep)
