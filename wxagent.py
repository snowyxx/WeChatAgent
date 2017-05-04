# encoding=utf-8

from multiprocessing.connection import Listener
from threading import Thread
import itchat
from itchat.content import TEXT
import pdb
import json
import re
import urllib
import urllib2
from conf import WECHATGROUP, SDPURL, SDPAPIKEY, OPMURL, OPMAPIKEY, LISTENERHOST, LISTENERPORT, TULINGKEY

address = (LISTENERHOST, LISTENERPORT)
listener = Listener(address)
runing = True


@itchat.msg_register(TEXT, isGroupChat=True)
def simple_reply(msg):
    text = msg['Content']
    requester = msg['ActualNickName']
    replyText = u'I received: {}\n'.format(msg['Content'])
    print replyText
    if msg['User']['NickName'] in WECHATGROUP:
        sdpaddrequest = re.match(r'(?i)(sdp) (add request) (.*)', text)
        opmgetdevice = re.match(r'(?i)(opm) (get) (\S*)', text)
        if sdpaddrequest:
            description = sdpaddrequest.group(3)
            postResp = addSdpRequest(requester, description)
            resp = json.loads(postResp)
            if resp['operation']['result']['status'] == u'Success':
                newRequestID = resp['operation']['Details']['WORKORDERID']
                replyText = u'{}的SDP工单已添加，工单号是：{}'.format(requester, newRequestID)
            else:
                replyText = u'{}的SDP工单添加失败，返回信息：\n{}'.format(requester, postResp)
        elif opmgetdevice:
            deviceName = opmgetdevice.group(3)
            postResp = getOpmDevice(deviceName)
            resp = json.loads(postResp)
            error = resp.get('error', '')
            if error:
                replyText = error.get('message', '')
            else:
                displayName = resp.get('displayName', '')
                displayCategory = resp.get('displayCategory', '')
                respTime = resp.get('responseTime', '')
                status = resp.get('statusStr', '')
                sysName = resp.get('sysName', '')
                typeStr = resp.get('type', '')
                managed = resp.get('managed', '')
                deviceProtocol = resp.get('deviceProtocol', '')
                availdata = resp['availdata']['Up']
                defaultDials = u'性能监视器：\n'
                for data in resp['defaultDials']:
                    defaultDials += u'\t\t - {}：{}\n'.format(data.get('displayName', ''), data.get('value', ''))
                replyText = u'名称：{}\n类别：{}\n响应时间：{}\n状态：{}\n型号：{}\n类型：{}\n是否被管：{}\n协议：{}\n可用性：{}\n{}\n'.format(displayName, displayCategory, respTime, status, sysName, typeStr, managed, deviceProtocol, availdata, defaultDials)
        else:
            replyText += json.loads(get_tuling(text)).get('text',u'没啥可说，大哥常来啊！')
    return replyText

'''
@itchat.msg_register(TEXT)
def other_reply(msg):
    print 'Not group?????'
    return u'I received:{}'.format(msg['Content'])
'''


def getOpmDevice(deviceName):
    print 'Get in getOpmDevice()'
    # url =  'http://192.168.0.96:8060/api/json/device/getDeviceSummary?isFluidic=true&name=192.168.0.18&apiKey=67b287274fb1be2b449f1653508b7669'
    url = '{}/api/json/device/getDeviceSummary?isFluidic=true&name={}&apiKey={}'.format(OPMURL, deviceName, OPMAPIKEY)
    response = urllib2.urlopen(url)
    print '   - Got response'
    return response.read().decode('UTF-8')


def addSdpRequest(requester, description):
    print 'Get in addSdpRequest()'
    # url = 'http://192.168.0.111:8050/sdpapi/request?TECHNICIAN_KEY=5C45F603-DF68-4CC1-BB66-E923670EC2BD'
    url = '{}/sdpapi/request?TECHNICIAN_KEY={}'.format(SDPURL, SDPAPIKEY)
    subject = u'来自微信的工单：组名：{}  用户名：{}'.format(u'运维告警', requester)
    inputdata = u'{"operation": {"details": {"requester": "%s", "subject": "%s", "description": "%s", "requesttemplate": "Unable to browse", "priority": "High", "site": "New York", "group": "Network", "technician": "Howard Stern", "level": "Tier 3", "status": "open", "service": "Email"}}}' % (requester, subject, description)
    postdata = {
        "format": 'json',
        "OPERATION_NAME": 'ADD_REQUEST',
        "INPUT_DATA": inputdata.encode('UTF-8')
    }
    print 'ADD_REQUEST -- %s' % postdata
    response = urllib2.urlopen(url=url, data=urllib.urlencode(postdata))
    print '   - Got response'
    return response.read().decode('UTF-8')


def get_tuling(msg):
    apiUrl = 'http://www.tuling123.com/openapi/api'
    data = {
        'key': TULINGKEY,
        'info': msg.encode('UTF-8'),
        'userid': 'wechat-robot',
    }
    response = urllib2.urlopen(url=apiUrl, data=urllib.urlencode(data))
    return response.read().decode('UTF-8')


def openConnection():
    while runing:
        conn = listener.accept()
        chatrooms = itchat.get_chatrooms()
        groupList = []
        print 'connection accepted from', listener.last_accepted

        data = conn.recv()
        print data
        try:
            for room in chatrooms:
                print room['NickName']
                if room['NickName'] in WECHATGROUP:
                    groupList.append(room)
            for group in groupList:
                wxresp = itchat.send(data, group['UserName'])
                conn.send_bytes('Wechat Response: {}'.format(wxresp['BaseResponse']['ErrMsg'].encode('utf-8')))
        except Exception, e:
            print e
            raise e
        finally:
            conn.close()


def closeConnection():
    global runing
    runing = False
    listener.close()

socket = Thread(target=openConnection)
socket.daemon = True
socket.start()
itchat.auto_login(hotReload=True, exitCallback=closeConnection)
itchat.run()
