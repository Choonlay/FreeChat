import itchat
import re
import mysql.connector
import random
import os
import time
from itchat.content import *
from concurrent.futures import ThreadPoolExecutor

# s mean start, p mean pause
START = 's'
PICTURE_PATH = './Resource/HappyPic/'
SONG_PATH = './Resource/HappySong/'
HEAD_PATH = './Resource/HeadImage/'
status = START
executor = ThreadPoolExecutor(max_workers=10)
festivalList = []
happyList = []
happyContentList = []
db = mysql.connector.connect(host='localhost', user='root', passwd='root', db='free_chat')
careTimeMap = {}
waitTime = 1 * 60
waitTimeInterval = 5


def is_admin(msg):
    return msg['FromUserName'] == msg['ToUserName']


def set_status(status_code):
    global status
    status = status_code

def saoraoHandle(object):
    global careTimeMap
    careTimeMap[object] = waitTime
    while True:
        tempTime = 0
        while tempTime > careTimeMap[object]:
            time.sleep(waitTimeInterval)
            tempTime += waitTimeInterval
        if (careTimeMap[object] == 0):
            itchat.send_msg('略略略', toUserName=object)
            careTimeMap[object] = waitTime
        itchat.send_msg('^_^', toUserName=object)

def saorao(object):
    global executor
    executor.submit(saoraoHandle, object)


def admin_control(msg):
    if (is_admin(msg)):
        if (msg['Type'] == 'Text'):
            commandList = msg['Content'].split('?')
            command = commandList[0]
            if (len(commandList) > 1):
                if (re.search('ss', command)):
                    set_status(commandList[1])
                elif (re.search('ah', command)):
                    cur = db.cursor()
                    cur.execute("INSERT INTO happy(happy) VALUES('%s')" % (commandList[1]))
                    db.commit()
                    global happyList
                    happyList.append(commandList[1])
                elif (re.search('af', command)):
                    cur = db.cursor()
                    cur.execute("INSERT INTO festival(festival_key, festival) VALUES(%d, '%s')" % (1, commandList[1]))
                    db.commit()
                    global festivalList
                    festivalList.append(commandList[1])
                elif (re.search('ahm', command)):
                    cur = db.cursor()
                    cur.execute("INSERT INTO happy_msg(festival_key, happy_content) VALUES(%d, '%s')" % (1, commandList[1]))
                    db.commit()
                    global happyContentList
                    happyContentList.append(commandList[1])
                elif (re.search('pr', command)):
                    friends = itchat.search_friends(commandList[1])
                    if (len(friends) > 0):
                        send_msg(friends[0]['UserName'], 1)
                elif (re.search('sr', command)):
                    srObject = itchat.search_friends(commandList[1])
                    if (len(srObject) > 0):
                        saorao(srObject[0]['UserName'])
                else:
                    itchat.send_msg('command not found', toUserName=msg['ToUserName'])
        elif (msg['Type'] == 'Picture'):
            msg.download(PICTURE_PATH + msg['FileName'])


def random_happy_content(festival_key):
    global happyContentList
    if(len(happyContentList) == 0):
        cur = db.cursor()
        cur.execute('SELECT happy_content FROM happy_msg WHERE festival_key = %d' % festival_key)
        results = cur.fetchall()
        for content in results:
            happyContentList.append(content[0])
    return happyContentList[random.randint(0, len(happyContentList) - 1)]


def send_msg(to_user_name, festival):
    random_sample = random.sample([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1], 2)
    itchat.send_msg(random_happy_content(festival), toUserName=to_user_name)
    if (random_sample[0] == 1):
        itchat.send_image(os.path.join(PICTURE_PATH, random.choice(os.listdir(PICTURE_PATH))), toUserName=to_user_name)
    if (random_sample[1] == 1):
        itchat.send('@fil@' + os.path.join(SONG_PATH, random.choice(os.listdir(SONG_PATH))), toUserName=to_user_name)
    head_image_uri = HEAD_PATH + to_user_name + '.jpg'
    print(head_image_uri)
    if (not os.path.exists(head_image_uri)):
        headImage = open(head_image_uri, 'wb')
        headImage.write(itchat.get_head_img(to_user_name))
        headImage.close()
    itchat.send_image(head_image_uri, toUserName=to_user_name)


def match_festival(content):
    for happy in happyList:
        if (re.search(happy, content)):
            for festival in festivalList:
                if (re.search(festival, content)):
                    return 1
            break
    return -1


@itchat.msg_register([TEXT, PICTURE, VIDEO, ATTACHMENT, SHARING], isFriendChat=True, isGroupChat=True, isMpChat=True)
def route(msg):
    fromUserName = msg['FromUserName']
    if(is_admin(msg)):
        admin_control(msg)
    else:
        if (status == START):
            #add care feature
            global careTimeMap
            careTimeMap[fromUserName] = 0

            festival = match_festival(msg['Content'])
            if (festival != -1):
                global executor
                executor.submit(send_msg, fromUserName, festival)


def init_happy_list():
    cur = db.cursor()
    cur.execute('SELECT happy FROM happy')
    results = cur.fetchall()
    global happyList
    happyList = []
    for content in results:
        happyList.append(content[0])


def init_festival_list():
    cur = db.cursor()
    cur.execute('SELECT festival FROM festival')
    results = cur.fetchall()
    global festivalList
    festivalList = []
    for content in results:
        festivalList.append(content[0])


def init():
    global status
    status = START
    init_happy_list()
    init_festival_list()


itchat.auto_login(hotReload=True)
init()
itchat.run()