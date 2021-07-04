#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-03 21:13:26
LastEditTime: 2021-07-04 12:56:34
Description: 异步&多线程下载抖音无水印视频
'''
import asyncio
from concurrent import futures
import aiohttp
import sqlite3
from Dy_del_wm import Dy
from concurrent.futures import ThreadPoolExecutor
import os
import sys
import queue
import threading
import re
import requests
import time
import traceback
import random


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


def do_load_media(video: tuple, path_raw):
    '''
    传入链接和路径下载视频,支持断点续传.
    path: 路径不包含文件
    抄袭自: https://blog.csdn.net/kuangshp128/article/details/86012288
    '''

    # video = video_queue.get(timeout=3)
    video_url = video[0]
    video_desc = video[1]

    file_name = checkNameValid(video_desc)

    path = os.path.join(path_raw, "%s.mp4" % (file_name))

    try:
        s_t = time.time()
        headers = {
            'User-Agent': random.choice(Dy().UAlist),
        }
        pre_content_length = 0
        # 循环接收视频数据
        while True:
            # 若文件已经存在，则断点续传，设置接收来需接收数据的位置
            if os.path.exists(path):
                headers['Range'] = 'bytes=%d-' % os.path.getsize(path)

            res = requests.get(video_url, stream=True, headers=headers)

            # 获取到的总长度

            content_length = int(res.headers['Content-Length'])
            # 若当前报文长度小于前次报文长度，或者已接收文件等于当前报文长度，则可以认为视频接收完成
            if content_length < pre_content_length or (
                    os.path.exists(path) and os.path.getsize(path) == content_length) or content_length == 0:
                break
            pre_content_length = content_length

            # 写入收到的视频数据
            with open(path, 'ab') as file:
                file.write(res.content)
                file.flush()
                # 下载进度
        e_t = time.time()

        print("文件:%s.mp4 下载完成:%.3fM 用时:%.2f" %
              (video_desc, os.path.getsize(path)/1024/1024, e_t-s_t))

    except Exception as e:

        print(res.status_code, traceback.format_exc())
        print("重试")
        # 这样会导致 path 不断叠加.
        do_load_media(video, path_raw)


def readSql(table_name) -> list:
    '''
    从数据库中的读取分享链接,返回一个列表
    '''
    conn = sqlite3.connect(os.path.join(sys.path[0], "dy.db"))
    c = conn.cursor()
    c.execute('SELECT * FROM main.%s;' % (table_name))
    return c.fetchall()


def getVideo(share_url, videoList):
    '''
    获取视频无水印链接和文案(生产者)
    传入url队列和视频队列
    '''

    result = Dy().main(share_url)

    if result["status"] == 1:
        print("线程%s出问题:" % (threading.current_thread().name), result)
        return

    video_url = result["data"]["video"]["video_url"]
    video_desc = result["data"]["video"]["desc"]
    video = (video_url, video_desc)
    # 添加元素到视频队列
    videoList.append(video)
    # video_queue.put(video)
    print("解析成功! %s" % (video_desc))


def mkdirInPath(name):
    '''
    在程序目录下新建文件夹,如果已存在就不创建.
    '''
    path = sys.path[0]
    new_dir = os.path.join(path, name)
    # print(path)
    if os.path.exists(new_dir):
        # print("目录:%s已存在" % (new_dir))
        return new_dir
    else:
        os.mkdir(new_dir)
        print("目录:%s创建成功" % (new_dir))
        return new_dir


if __name__ == "__main__":

    table_name = "common"
    mkdirInPath(table_name)
    # video_queue = queue.Queue()
    videoList = []
    path = os.path.join(sys.path[0], table_name)

    with ThreadPoolExecutor() as pool:
        for text, url in readSql(table_name):
            pool.submit(getVideo, url, videoList)

    print("一共有%s条视频,等待3s后下载" % (len(videoList)))

    with ThreadPoolExecutor() as pool2:
        for video in videoList:
            # print(video)
            pool2.submit(do_load_media, video, path)

    # 测试
    # for video in videoList:
    #     do_load_media(video, path)
