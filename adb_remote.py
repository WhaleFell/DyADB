'''`
Author: whalefall
Date: 2021-06-29 18:04:27
LastEditTime: 2021-06-30 16:11:03
Description: 抖音adb自动刷,实现两个线程,一个线程负责下载,一个线程负责调动adb.
'''
from Dy_del_wm import Dy
import os
import sqlite3
from time import sleep
import subprocess
import re
import sys
from urllib.parse import quote
import requests
import threading
import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
# 获取剪切板内容


def getCopy():
    '''
    获取剪贴板内容,返回(文案,链接)
    '''
    try:
        # 开启另一个管道运行获取剪切板内容
        c = subprocess.check_output(
            'adb shell am broadcast -a clipper.get').decode()

        print(c)
        # 匹配网址的正则表达式
        pat = re.compile(r"[a-zA-z]+://[^\s]*")
        url = pat.search(c)[0]
        # print(url)

        pat2 = re.compile(r"([\u4e00-\u9fa5].*?[\u4e00-\u9fa5])")
        text = pat2.findall(c)
        text = ''.join(text)
        # print(text)
    except Exception as e:
        print("匹配失败")
        return "None", "None"
    else:
        # print(text, url)
        return text, url

# sqlite3数据库


def writeSQL(Text, Url, tableName="common"):
    '''
    读写sqlite数据库
    '''
    conn = sqlite3.connect("dy.db")
    c = conn.cursor()

    # 新建表
    c.execute('''
    create table if not exists `{}` (
        `Text` varchar(225),
        `Url` varchar(225),
        primary key(`Text`)
    )
    '''.format(tableName))

    conn.commit()

    try:
        c.execute('''
        insert into `{}` (Text, Url) values (?,?)
        '''.format(tableName), (Text, Url))

        conn.commit()
    except sqlite3.IntegrityError:
        print("数据重复! Text:%s" % (Text))
        return "0"
    except Exception as e:
        print("插入数据库出现未知错误! %s" % (e))
        return "ERROR"
    else:
        print("插入数据成功! Text:%s" % (Text))
        return "1"


# 若检测到有多次重复的情况 -> 即 点击失误/加载过长/剪切板服务挂了 重新打开app


def restartDyApp():
    '''
    重新打开抖音app
    '''
    # 启动剪切板服务
    os.system("adb shell am startservice ca.zgrs.clipper/.ClipboardService")

    # 点击2次返回到桌面的主页面
    os.system("adb shell input tap 548 1860")
    sleep(0.5)
    os.system("adb shell input tap 548 1860")
    sleep(0.5)

    # 打开多任务
    os.system("adb shell input tap 815 1872")
    sleep(0.5)

    # 上划将 抖音APP 删除后台
    os.system("adb shell input swipe 555 1332 555 337")
    sleep(0.5)

    # 点击2次返回到桌面的主页面
    os.system("adb shell input tap 548 1860")
    os.system("adb shell input tap 548 1860")
    sleep(0.5)

    # 点击 抖音app 并等待
    os.system("adb shell input tap 162 230")
    sleep(18)
    print("重启抖音app可能成功!")

    return


def do_load_media(url, path):
    '''
    传入链接和路径下载视频,支持断点续传.
    抄袭自: https://blog.csdn.net/kuangshp128/article/details/86012288
    '''
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko)'}
        pre_content_length = 0
        # 循环接收视频数据
        while True:
            # 若文件已经存在，则断点续传，设置接收来需接收数据的位置
            if os.path.exists(path):
                headers['Range'] = 'bytes=%d-' % os.path.getsize(path)
            res = requests.get(url, stream=True, headers=headers)
            content_length = int(res.headers['content-length'])

            # 若当前报文长度小于前次报文长度，或者已接收文件等于当前报文长度，则可以认为视频接收完成
            if content_length < pre_content_length or (
                    os.path.exists(path) and os.path.getsize(path) == content_length) or content_length == 0:
                break

            pre_content_length = content_length

            # 写入收到的视频数据
            with open(path, 'ab') as file:
                file.write(res.content)
                file.flush()
                print('%s下载成功,file size : %dtotal size:%d' %
                      (path, os.path.getsize(path), content_length))
    except Exception as e:
        print("视频%s下载错误:%s" % (path, e))


def checkNameValid(name=None):
    """
    检测Windows文件名称！
    抄袭自: https://blog.csdn.net/tianzhaixing2013/article/details/53184934
    """
    if name is None:
        print("name is None!")
        return
    reg = re.compile(r'[\\/:*?"<>|\r\n]+')
    valid_name = reg.findall(name)
    if valid_name:
        for nv in valid_name:
            name = name.replace(nv, "_")
    return name


def downloadVidoe(path_dir):
    '''
    不断获取队列中的视频信息元组下载视频.
    '''

    while True:
        try:
            videoTuple = video_queue.get(timeout=3)
            video_text = videoTuple[0]
            video_url = videoTuple[1]
            api_json = Dy().main(video_url)
            name = api_json["data"]["video"]["desc"]
            name = checkNameValid(name)
            url = api_json["data"]["video"]["video_url"]
            path_full = os.path.join(path_dir, "%s.mp4" % (name))
            do_load_media(url, path_full)
            video_queue.task_done()
        except queue.Empty:
            # print("空")
            continue
        except Exception as e:
            print("线程%s出现异常%s" %
                  (threading.current_thread().name, traceback.format_exc()))
        finally:
            # video_queue.task_done()
            pass


if __name__ == "__main__":
    # 数据重复计数器
    count = 0
    # 复制视频链接队列

    video_queue = queue.Queue()

    # with ThreadPoolExecutor(max_workers=5) as pool:
    #     for i in range(6):
    #         pool.submit(downloadVidoe,os.path.join(sys.path[0],"common"))

    # print("Main")
    threadList = [
        threading.Thread(target=downloadVidoe, args=(
            os.path.join(sys.path[0], "common"),), name=i)
        for i in range(6)
    ]

    for thread_ in threadList:
        thread_.setDaemon(True)
        thread_.start()

    status_lock = 0 # 打算设置机制
    while True:

        # 点击分享按钮
        os.system("adb shell input tap 998 1296")
        sleep(0.1)
        # 点击复制链接按钮
        os.system("adb shell input tap 154 1492")
        # sleep(0.2)
        # 获取剪切板
        text, url = getCopy()
        sql_result = writeSQL(Text=text, Url=url)

        # 没有与数据库中的重复就提交到队列,并调整状态锁
        if sql_result == "1":
            video_queue.put((text, url))
            status_lock = 0

        if count >= 10:
            print("数据已重复三次,准备重启 抖音APP")
            restartDyApp()
            # 还原计数器
            count = 0

        if sql_result == "0":
            count += 1
            print("数据重复第%s次数" % (count))

        # 下滑
        os.system("adb shell input swipe 520 1400 536 599")

    # print(getCopy())
