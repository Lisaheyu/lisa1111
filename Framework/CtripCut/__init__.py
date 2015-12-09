#-*- coding:utf-8 -*-
import re
import time
import math
import os,sys
import pprint
import finalseg
import time
import tempfile
import marshal
from math import log
import random
from posseg import viterbi as viterbi
default_encoding = sys.getfilesystemencoding()


class CnlpCut:
    def __init__(self, dict_name, cache_name):
        self.FREQ = {}
        self.total = 0.0
        self.trie = {}
        self.min_freq = 0.0
        self.dict_name = 'dict/%s' % dict_name
        self.cache_name = cache_name
        self.create_dict()

    def create_dict(self):
        _curpath=os.path.normpath( os.path.join( os.getcwd(), os.path.dirname(__file__) ) )
        print >> sys.stderr, "Building Trie for %s" % self.dict_name
        t1 = time.time()
        cache_file = os.path.join(tempfile.gettempdir(),self.cache_name)
        load_from_cache_fail = True
        if os.path.exists(cache_file) and os.path.getmtime(cache_file)>os.path.getmtime(os.path.join(_curpath,self.dict_name)):
            print >> sys.stderr, "loading model from cache"
            try:
                self.trie,self.FREQ,self.total,self.min_freq = marshal.load(open(cache_file,'rb'))
                load_from_cache_fail = False
            except:
                load_from_cache_fail = True
        if load_from_cache_fail:
            self.trie,self.FREQ,self.total = self.gen_trie()
            self.FREQ = dict([(k,log(float(v)/self.total)) for k,v in self.FREQ.iteritems()]) #normalize
            self.min_freq = min(self.FREQ.itervalues())
            print >> sys.stderr, "dumping model to file cache"
            tmp_suffix = "."+str(random.random())
            marshal.dump((self.trie,self.FREQ,self.total,self.min_freq),open(cache_file+tmp_suffix,'wb'))
            if os.name=='nt':
                import shutil
                replace_file = shutil.move
            else:
                replace_file = os.rename
            replace_file(cache_file+tmp_suffix,cache_file)

        print >> sys.stderr, "loading model cost ", time.time() - t1, "seconds."
        print >> sys.stderr, "Trie has been built succesfully."

    def gen_trie(self):
        lfreq = {}
        trie = {}
        ltotal = 0.0
        _curpath=os.path.normpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        dict_path = os.path.join(_curpath, self.dict_name)
        content = open(dict_path,'rb').read().decode('utf-8')
        lines = content.split("\n")
        for idx,line in enumerate(lines):
            if len(line.split(" ")) != 3:
                print 'line:%s, wrong format!' % idx
                continue
            word,freq,_ = line.split(" ")
            freq = float(freq)
            lfreq[word] = freq
            ltotal+=freq
            p = trie
            for c in word:
                if not c in p:
                    p[c] ={}
                p = p[c]
            p['']='' #ending flag
        return trie,lfreq,ltotal

    def __cut_all(self, sentence):
        dag = self.get_DAG(sentence)
        old_j = -1
        for k,L in dag.iteritems():
            if len(L)==1 and k>old_j:
                yield sentence[k:L[0]+1]
                old_j = L[0] 
            else:
                for j in L:
                    if j>k:
                        yield sentence[k:j+1]
                        old_j = j

    def calc(self,sentence,DAG,idx,route):
        N = len(sentence)
        route[N] = (1.0,'')
        for idx in xrange(N-1,-1,-1):
            candidates = [ ( self.FREQ.get(sentence[idx:x+1],self.min_freq) + route[x+1][0],x ) for x in DAG[idx] ]
            route[idx] = max(candidates)

    def get_DAG(self,sentence):
        N = len(sentence)
        i,j=0,0
        p = self.trie
        DAG = {}
        while i<N:
            c = sentence[j]
            if c in p:
                p = p[c]
                if '' in p:
                    if not i in DAG:
                        DAG[i]=[]
                    DAG[i].append(j)
                j+=1
                if j>=N:
                    i+=1
                    j=i
                    p=self.trie
            else:
                p = self.trie
                i+=1
                j=i
        for i in xrange(len(sentence)):
            if not i in DAG:
                DAG[i] =[i]
        return DAG

    def __cut_DAG(self,sentence):
        DAG = self.get_DAG(sentence)
        route ={}
        self.calc(sentence,DAG,0,route=route)
        x = 0
        buf =u''
        N = len(sentence)
        while x<N:
            y = route[x][1]+1
            l_word = sentence[x:y]
            if y-x==1:
                buf+= l_word
            else:
                if len(buf)>0:
                    if len(buf)==1:
                        yield buf
                        buf=u''
                    else:
                        regognized = finalseg.cut(buf)
                        for t in regognized:
                            yield t
                        buf=u''
                yield l_word        
            x =y
    
        if len(buf)>0:
            if len(buf)==1:
                yield buf
            else:
                regognized = finalseg.cut(buf)
                for t in regognized:
                    yield t

    def cut(self,sentence,cut_all=False):
        if not ( type(sentence) is unicode):
            try:
                sentence = sentence.decode('utf-8')
            except:
                sentence = sentence.decode('gbk','ignore')
        re_han, re_skip = re.compile(ur"([\u4E00-\u9FA5a-zA-Z0-9+#]+)"), re.compile(ur"[^\r\n]")
        if cut_all:
            re_han, re_skip = re.compile(ur"([\u4E00-\u9FA5]+)"), re.compile(ur"[^a-zA-Z0-9+#\n]")
        blocks = re_han.split(sentence)
        cut_block = self.__cut_DAG
        if cut_all:
            cut_block = self.__cut_all
        for blk in blocks:
            if re_han.match(blk):
                    #pprint.pprint(__cut_DAG(blk))
                    for word in cut_block(blk):
                        yield word
            else:
                tmp = re_skip.split(blk)
                for x in tmp:
                    if x!="":
                        yield x

    def cut_for_search(self,sentence):
        words = self.cut(sentence)
        for w in words:
            if len(w)>2:
                for i in xrange(len(w)-1):
                    gram2 = w[i:i+2]
                    if gram2 in self.FREQ:
                        yield gram2
            if len(w)>3:
                for i in xrange(len(w)-2):
                    gram3 = w[i:i+3]
                    if gram3 in self.FREQ:
                        yield gram3
            yield w

    def load_userdict(self,f):
        if isinstance(f, (str, unicode)):
            f = open(f, 'rb')
        content = f.read().decode('utf-8')
        for line in content.split("\n"):
            if line.rstrip()=='': continue
            word,freq = line.split(" ")
            freq = float(freq)
            self.FREQ[word] = log(freq / self.total)
            p = self.trie
            for c in word:
                if not c in p:
                    p[c] ={}
                p = p[c]
            p['']='' #ending flag    


class pair(object):
    def __init__(self,word,flag):
        self.word = word
        self.flag = flag

    def __unicode__(self):
        return self.word+u"/"+self.flag

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__unicode__().encode(default_encoding)

    def encode(self,arg):
        return self.__unicode__().encode(arg)


class CnlpTag:
    def __init__(self, cnlp_cut):
        self.prob_start = self.load_model("posseg/prob_start.py")
        self.prob_trans = self.load_model("posseg/prob_trans.py")
        self.prob_emit = self.load_model("posseg/prob_emit.py")
        self.char_state_tab = self.load_model("posseg/char_state_tab.py")
        self.word_tag_tab = self.load_model(cnlp_cut.dict_name)
        self.cnlp_cut = cnlp_cut

    def load_model(self, f_name):
        _curpath=os.path.normpath( os.path.join( os.getcwd(), os.path.dirname(__file__) )  )
        prob_p_path = os.path.join(_curpath,f_name)
        if f_name.endswith(".py"):
            return eval(open(prob_p_path,"rb").read())
        else:
            result = {}
            for idx,line in enumerate(open(prob_p_path,"rb")):
                line = line.strip()
                if line=="":continue
                if len(line.split(' ')) != 3:
                    print idx
                    continue
                word, _, tag = line.split(' ')
                result[word.decode('utf-8')]=tag
        return result

    def __cut(self, sentence):
        prob, pos_list =  viterbi.viterbi(sentence, self.char_state_tab, self.prob_start, self.prob_trans, self.prob_emit)
        begin, next = 0,0
    
        for i,char in enumerate(sentence):
            pos = pos_list[i][0]
            if pos=='B':
                begin = i
            elif pos=='E':
                yield pair(sentence[begin:i+1], pos_list[i][1])
                next = i+1
            elif pos=='S':
                yield pair(char,pos_list[i][1])
                next = i+1
        if next<len(sentence):
            yield pair(sentence[next:], pos_list[next][1] )

    def __cut_detail(self, sentence):
        re_han, re_skip = re.compile(ur"([\u4E00-\u9FA5]+)"), re.compile(ur"[^a-zA-Z0-9+#\r\n]")
        re_eng,re_num = re.compile(ur"[a-zA-Z+#]+"), re.compile(ur"[0-9]+")
        blocks = re_han.split(sentence)
        for blk in blocks:
            if re_han.match(blk):
                for word in self.__cut(blk):
                    yield word
            else:
                tmp = re_skip.split(blk)
                for x in tmp:
                    if x!="":
                        if re_num.match(x):
                            yield pair(x,'m')
                        elif re_eng.match(x):
                            yield pair(x,'eng')
                        else:
                            yield pair(x,'x')

    def __cut_DAG(self, sentence):
        DAG = self.cnlp_cut.get_DAG(sentence)
        route ={}
        
        self.cnlp_cut.calc(sentence,DAG,0,route=route)
    
        x = 0
        buf =u''
        N = len(sentence)
        while x<N:
            y = route[x][1]+1
            l_word = sentence[x:y]
            if y-x==1:
                buf+= l_word
            else:
                if len(buf)>0:
                    if len(buf)==1:
                        yield pair(buf, self.word_tag_tab.get(buf,'x'))
                        buf=u''
                    else:
                        regognized = self.__cut_detail(buf)
                        for t in regognized:
                            yield t
                        buf=u''
                yield pair(l_word, self.word_tag_tab.get(l_word,'x'))
            x =y
    
        if len(buf)>0:
            if len(buf)==1:
                yield pair(buf, self.word_tag_tab.get(buf,'x'))
            else:
                regognized = self.__cut_detail(buf)
                for t in regognized:
                    yield t

    def cut(self, sentence):
        if not ( type(sentence) is unicode):
            try:
                sentence = sentence.decode('utf-8')
            except:
                sentence = sentence.decode('gbk','ignore')
        re_han, re_skip = re.compile(ur"([\u4E00-\u9FA5a-zA-Z0-9+#]+)"), re.compile(ur"[^\r\n]")
        re_eng,re_num = re.compile(ur"[a-zA-Z+#]+"), re.compile(ur"[0-9]+")
        blocks = re_han.split(sentence)
        for blk in blocks:
            if re_han.match(blk):
                for word in self.__cut_DAG(blk):
                    yield word
            else:
                tmp = re_skip.split(blk)
                for x in tmp:
                    if x!="":
                        if re_num.match(x):
                            yield pair(x,'m')
                        elif re_eng.match(x):
                            yield pair(x,'eng')
                        else:
                            yield pair(x,'x')

    def cut_for_search(self,sentence):
        word_list = self.cnlp_cut.cut_for_search(sentence)

        for word in word_list:
            if word in self.word_tag_tab:
                yield pair(word, self.word_tag_tab[word])
            else:
                yield pair(word, 'x')



if __name__ == '__main__':
    a = CnlpCut('base_dict.txt', 'base.cache')
    b = CnlpTag(a)
    #a.create_dict()
    start = time.time()
    mess = '广州路线'
    print 'spend time: %s' % (time.time()-start)
    for i in b.cut(mess):
        print i.word, i.flag
