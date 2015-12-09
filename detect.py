#!/usr/bin/python
#coding=utf-8

import urllib
import urllib2
import time
import os
import sys
import socket

def restart_cnlp():
    os.system('sudo python /opt/cnlp/cnlp.py -stop')
    os.system('sudo python /opt/cnlp/cnlp.py -start&')

def send_mail(server_ip):
    sendmail_cmd = "echo 'hi:\n %s cnlp server error.\n please check quickly!' | "\
                   "mail -s 'cnlp server error!' wang_wei@ctrip.com -- -f wang_wei@ctrip.com" % server_ip
    os.system(sendmail_cmd)

def post(url, data, timeout):
    try:
        req = urllib2.Request(url)
        data = urllib.urlencode(data)
        #enable cookie
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, data, timeout= timeout)
        return response.code, response.read()
    except urllib2.HTTPError, e:
        return e.code,''
    except urllib2.URLError, e:
        if isinstance(e.reason, socket.timeout):
            return 'timeout',''
        else:
            # reraise the original error  
            raise

def post_request():
    posturl = "http://localhost/Parse"
    data = {'SourceText':'故宫附近的酒店', 'UserCity':'上海'}
    return post(posturl, data, timeout=1)

if __name__ == '__main__':
    count = 0
    '''
    while True:
        post_result = post_request()
        status_code = post_result[0]
        if status_code == 200:
            pass
        else:
            count += 1
        if count > 10:
            send_mail('192.168.79.197')
            #restart_cnlp()
            count = 0
        time.sleep(1)
    '''
    start = time.time()
    x = post_request()
    print x[0]
    print 'spend time:%s' % (time.time()-start)
