# -*- coding: utf-8 -*-
'''
__author__ = 'wang_wei@ctrip.com'
__copyright__ = 'CTI.ctrip.com'
__function__ = 'livechatApi'

'''
#import ujson
import sys
import os
import xlrd
import xlwt
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, _app_ctx_stack
from flask import send_from_directory

from werkzeug import secure_filename
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
ALLOWED_EXTENSIONS_2 = set(['txt'])

FILE_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append('%s/../../Framework' % FILE_PATH)
sys.path.append('%s/../../Logic' % FILE_PATH)

UPLOAD_FOLDER = '%s/upload' % FILE_PATH
DICT_FOLDER = '%s/dict_for_score' % FILE_PATH
#user status dict
USER_STATUS = {}


from PreProcess import preprocess as pp

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


#判断文件格式
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def allowed_file2(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS_2
#def change_basedict():


#读取文件（dict）
def readfile(filename):
    score_list = []
    word_list = []
    content = open(filename,'r')
    s = content.readlines()
    for i in s:
        i = i.replace('\n','')
        list_i = i.split(',')
        #print list_i
        word_i = list_i[0]
        #print  word_i
        score_i = list_i[1]
        
        score_list.append(score_i)
        word_list.append(word_i)
    content.close()
    return score_list, word_list

def add_to_basedict(wordlist):
    with open('/opt/getscore/Framework/CtripCut/dict/base_out.dict','a+') as rwf:
        for i in wordlist:
            #print i
            line = i + ' ' + str(10000)+ ' pf'+'\n'
            #print line
            rwf.write(line)
       
         
       
def savetobasedict():    
      #to read different dimension data
    xj_scorelist, xj_wordlist = readfile('%s/dict_for_score/xiaoji.txt'  % FILE_PATH)
    sx_scorelist, sx_wordlist = readfile('%s/dict_for_score/shouxian.txt' % FILE_PATH)
    xs_scorelist, xs_wordlist = readfile('%s/dict_for_score/xieshi.txt' % FILE_PATH)
    jt_scorelist, jt_wordlist = readfile('%s/dict_for_score/juti.txt'  % FILE_PATH)
    fq_scorelist, fq_wordlist = readfile('%s/dict_for_score/fangqi.txt' % FILE_PATH)
    fqx_scorelist, fqx_wordlist = readfile('%s/dict_for_score/fangqixia.txt' % FILE_PATH)
    dd1_scorelist, dd1_wordlist = readfile('%s/dict_for_score/daiding1.txt' % FILE_PATH)
    dd2_scorelist, dd2_wordlist = readfile('%s/dict_for_score/daiding2.txt' % FILE_PATH)
    
    command = 'sudo cp /opt/getscore/Framework/CtripCut/dict/base_dict.txt /opt/getscore/Framework/CtripCut/dict/base_out.dict'
    os.system(command)
    #add the word to the dict
    if xj_wordlist !=[]:
        add_to_basedict(xj_wordlist)
    if sx_wordlist !=[]:
        add_to_basedict(sx_wordlist)
    if xs_wordlist !=[]:
        add_to_basedict(xs_wordlist)
    if jt_scorelist !=[]:
        add_to_basedict(jt_wordlist)
    if fq_scorelist !=[]:
        add_to_basedict(fq_wordlist)
    if fqx_scorelist !=[]:
        add_to_basedict(fqx_wordlist)
    if dd1_scorelist !=[]:
        add_to_basedict(dd1_wordlist)
    if dd2_scorelist !=[]:
        add_to_basedict(dd2_wordlist)
    
    
def process_excel(uploadfilepath):
    #上传文件
    data = xlrd.open_workbook(uploadfilepath)

    #to read different dimension data
    xj_scorelist, xj_wordlist = readfile('%s/dict_for_score/xiaoji.txt'  % FILE_PATH)
    sx_scorelist, sx_wordlist = readfile('%s/dict_for_score/shouxian.txt' % FILE_PATH)
    xs_scorelist, xs_wordlist = readfile('%s/dict_for_score/xieshi.txt' % FILE_PATH)
    jt_scorelist, jt_wordlist = readfile('%s/dict_for_score/juti.txt'  % FILE_PATH)
    fq_scorelist, fq_wordlist = readfile('%s/dict_for_score/fangqi.txt' % FILE_PATH)
    fqx_scorelist, fqx_wordlist = readfile('%s/dict_for_score/fangqixia.txt' % FILE_PATH)
    dd1_scorelist, dd1_wordlist = readfile('%s/dict_for_score/daiding1.txt' % FILE_PATH)
    dd2_scorelist, dd2_wordlist = readfile('%s/dict_for_score/daiding2.txt' % FILE_PATH)

#to create new file to store the data

    file_out  = xlwt.Workbook()
    table_out = file_out.add_sheet('out_table')
    table = data.sheets()[0]
    nrows = table.nrows
    ncols = table.ncols

    table_out.write(0,13,u'消极')
    table_out.write(0,14,u'受限')
    table_out.write(0,15,u'写实')
    table_out.write(0,16,u'具体')
    table_out.write(0,17,u'放弃本次订单')
    table_out.write(0,18,u'放弃下次订单')
    table_out.write(0,19,u'待定')
    table_out.write(0,20,u'待定')

    for i in range(nrows):
        string_xj = ''
        string_sx = ''
        string_xs = ''
        string_jt = ''
        string_fq = ''
        string_fqx = ''
        string_dd1 = ''
        string_dd2 = ''
        value_of_row = table.row_values(i)
        col_index = 0
        for item in value_of_row:

            table_out.write(i,col_index,item)
            col_index = col_index + 1

        comments = table.cell(i,4).value
        xj_dict = []
        sx_dict = []
        xs_dict = []
        jt_dict = []
        fq_dict = []
        fqx_dict = []
        dd1_dict = []
        dd2_dict = []
        string_xj_all = ''
        string_sx_all = ''
        string_xs_all = ''
        string_jt_all = ''
        string_fq_all = ''
        string_fqx_all = ''
        string_dd1_all = ''
        string_dd2_all = ''
        if type(comments) == float or type(comments) == int:
            comments = ''
        word_c,tag_c = pp.cut_base(comments)
        for item_c in word_c:
            if tag_c[word_c.index(item_c)]== 'pf':
                #for 消极
                item_c_cc = item_c.encode('utf-8')
                #for 消极方面的词（dict 1）
                if item_c_cc in xj_wordlist:
                    #print item_c_cc
                    xj_index = xj_wordlist.index(item_c_cc)
                    score_xiaoji = xj_scorelist[xj_index]
                    string_xj = item_c + ' ' + str(score_xiaoji)+'\n'
                    if string_xj not in xj_dict:
                        xj_dict.append(string_xj)

               #for 受限方方面的词(dict 2)
                if item_c_cc in sx_wordlist:
                    sx_index = sx_wordlist.index(item_c_cc)
                    score_shouxian = sx_scorelist[sx_index]
                    string_sx = item_c + ' ' + str(score_shouxian)+'\n'
                    #print string_sx
                    if string_sx not in sx_dict:
                        sx_dict.append(string_sx)
                    #print sx_dict

               #for 写实方面的词(dict 3)
                if item_c_cc in xs_wordlist:
                    xs_index = xs_wordlist.index(item_c_cc)
                    score_xieshi = xs_scorelist[xs_index]
                    string_xs = item_c + ' ' + str(score_xieshi)+'\n'
                    if string_xs not in xs_dict:
                        xs_dict.append(string_xs)

              #for 具体方面的词(dict 4)
                if item_c_cc in jt_wordlist:
                    jt_index = jt_wordlist.index(item_c_cc)
                    score_juting = jt_scorelist[jt_index]
                    string_jt = item_c + ' ' + str(score_juting)+'\n'
                    if string_jt not in jt_dict:
                        jt_dict.append(string_jt)

               #for 放弃本次订单方面的词(dict 5)
                if item_c_cc in fq_wordlist:
                    fq_index = fq_wordlist.index(item_c_cc)
                    score_fangqi = fq_scorelist[fq_index]
                    string_fq = item_c + ' ' + str(score_fangqi)+'\n'
                    if string_fq not in fq_dict:
                        fq_dict.append(string_fq)

              #for 放弃下次订单方面的词(dict 6)
                if item_c_cc in fqx_wordlist:
                    fqx_index = fqx_wordlist.index(item_c_cc)
                    score_fangqixi = fqx_scorelist[fqx_index]
                    string_fqx = item_c + ' ' + str(score_fangqixi)+'\n'
                    #print string_fqx
                    if string_fqx not in fqx_dict:
                        fqx_dict.append(string_fqx)

              #for 待定的词(dict 7)
                if item_c_cc in dd1_wordlist:
                    dd1_index = dd1_wordlist.index(item_c_cc)
                    score_daiding1 = dd1_scorelist[dd1_index]
                    string_dd1 = item_c + ' ' + str(score_daiding1)+'\n'
                    if string_dd1 not in dd1_dict:
                        dd1_dict.append(string_dd1)

              #for 待定的词(dict 8)
                if item_c_cc in dd2_wordlist:
                    dd2_index = dd2_wordlist.index(item_c_cc)
                    score_daiding2 = dd2_scorelist[dd2_index]
                    string_dd2 = item_c + ' ' + str(score_daiding2)+'\n'
                    if string_dd2 not in dd2_dict:
                        dd2_dict.append(string_dd2)
        for item in xj_dict:
            string_xj_all = string_xj_all + item
        #print string_xj_all
        #print sx_dict
        for item in sx_dict:
            string_sx_all = string_sx_all + item

        for item in xs_dict:
            string_xs_all = string_xs_all + item

        for item in jt_dict:
            string_jt_all = string_jt_all + item

        for item in fq_dict:
            string_fq_all = string_fq_all + item
        #print fqx_dict
        for item in fqx_dict:
            string_fqx_all = string_fqx_all + item

        for item in dd1_dict:
            string_dd1_all = string_dd1_all + item

        for item in dd2_dict:
            string_dd2_all = string_dd2_all + item

 
        if i>0:
            table_out.write(i,13,string_xj_all)
            table_out.write(i,14,string_sx_all)
            #print string_sx_all
            table_out.write(i,15,string_xs_all)
            table_out.write(i,16,string_jt_all)
            table_out.write(i,17,string_fq_all)
            table_out.write(i,18,string_fqx_all)
            table_out.write(i,19,string_dd1_all)
            table_out.write(i,20,string_dd2_all)
    #command = 'sudo rm /opt/getscore/Framework/CtripCut/dict/base_out.dict'
    #os.system(command)

    file_out.save('%s/table_out.xls' % UPLOAD_FOLDER)
    return 'table_out.xls'

@app.route('/index')
def index():
    user = { 'nickname': 'Miguel' }
    posts = [
        { 
            'author': { 'nickname': 'John' }, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': { 'nickname': 'Susan' }, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template("index.html",
        title = 'Home',
        user = user,
        posts = posts)

@app.route('/test')
def test():
    return "hello world!"

#上传文件和处理文件
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, fname))
            uploadfilepath = os.path.join(UPLOAD_FOLDER, fname)
            outurl = process_excel(uploadfilepath)
            download_url = 'http://192.168.1.1:8082%s' % outurl
        
            #return download_url
            #return render_template('download.html',filepath = download_url) 
            #return render_template('download.html',filepath = outurl)
            #return redirect(url_for('uploaded_file',filename=filename))
            return send_from_directory(UPLOAD_FOLDER,outurl, as_attachment=True)
        else:
            return "please upload excel format document"


@app.route('/changedict', methods=['GET', 'POST'])
def changedict():
    if request.method == 'GET':
        return render_template('changedict.html')

    if request.method == 'POST':
        file = request.files['file']
        
        if file and allowed_file2(file.filename):
            fname = secure_filename(file.filename)
            file.save(os.path.join(DICT_FOLDER, fname))
            command1 = 'dos2unix %s'% os.path.join(DICT_FOLDER, fname)
            os.system(command1)
            savetobasedict()
            #command2 = 'sudo python /opt/getscore/getscore.py -restart'
            #os.system(command2) 
            #return '%s save successfully' % fname
            return '''
            <!doctype html>
            <a href=http://192.168.81.207:8084/stop>上传成功，先暂停服务</a>
            '''
            
        else:
            return "please upload txt format document"
if __name__ == '__main__':
   #上传文件
   #print UPLOAD_FOLDER
   filename = 'UED.xlsx'
   savetobasedict()
   process_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
   app.run()
