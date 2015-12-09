#-*- coding:utf-8 -*-

import os
import time
import sys

FILE_PATH = os.path.split(os.path.realpath(__file__))[0]
CMD_UWSGI = 'uwsgi -s 127.0.0.1:9003 --pythonpath %s/Presentation/CnlpApi '\
            '-w CnlpApi:app -d %s/Log/uwsgi.log --post-buffering 8192 '\
            '-p 2 --socket-timeout 10 --listen 120 --harakiri 60 ' % (FILE_PATH, FILE_PATH)
#CMD_TRAIN = 'python %s/Presentation/CrobotServer/TrainFromSql.py' % FILE_PATH

def find_uwsgi():
    CMD_GREP = 'ps aux|grep uwsgi'
    lines = os.popen(CMD_GREP).readlines()
    for i in lines:
       if i.find(CMD_UWSGI[0:60]) != -1:
           return True
    return False

def get_cmd_pid(CMD):
    listOfID = []
    CMD_GREP = 'ps aux|grep %s' % 'python'
    lines = os.popen(CMD_GREP).readlines()
    for line in lines:
        if line.find(CMD) != -1:
            flag = True
            mid = ''
            for idx,s in enumerate(line):
                if s == ' ' and flag == True:
                    mid += s
                    flag = False
                elif s != ' ':
                    mid += s
                    flag = True
            line = mid
            listOfID.append(line.split(' ')[1])

    return listOfID

def reload_log(CMD):
    with open(('%s/Log/reload.log' % FILE_PATH),'a') as f:
        log = '%s restart %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),CMD)
        f.write(log)

def stop_uwsgi():
    #停止监控程序
    listOfPid = get_cmd_pid('getscore.py -start')
    for pid in listOfPid:
        os.system('sudo kill -9 %s' % pid)
    #停止相关uwsgi
    listOfPid = get_cmd_pid(CMD_UWSGI[0:60])
    for pid in listOfPid:
        os.system('sudo kill -9 %s' % pid)

if __name__ == '__main__':
    if sys.argv[1] == '-start':
        while(True):
            if not find_uwsgi():
                reload_log(CMD_UWSGI)
                os.system(CMD_UWSGI)
            #if not find_train():
                #reload_log(CMD_TRAIN)
                #os.system(CMD_TRAIN)
            time.sleep(2)
    elif sys.argv[1] == '-stop':
        #listOfPid = get_cmd_pid('getscore_p.py -start')
        #for pid in listOfPid:
            #os.system('sudo kill -9 %s' % pid)
        #os.system('sudo killall -9 uwsgi')
        stop_uwsgi()
        print 'GETSCORE has stoped!'
    elif sys.argv[1] == '-restart':
        stop_uwsgi()
        os.system('sudo python getscore.py -start&')
        print 'CnlpAssistant has restarted!'
    else:
        print 'the parameter is not correct!'
        print '--->%s: start CnlpAssistant' % '-start'
        print '--->%s: stop CnlpAssistant' % '-stop'
        print '--->%s: restart CnlpAssistant' % '-restart'
