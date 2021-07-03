#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-02 19:53:05
LastEditTime: 2021-07-03 17:06:22
Description: 提取 sqlite 数据库里面的链接,通过多线程技术(生产者消费者模型)下载,抖音去水印不依赖外部api
'''
import sqlite3
from Dy_del_wm import Dy
import os
import sys
import queue
import threading
import requests
import re


def readSql(table_name) -> list:
    '''
    从数据库中的读取分享链接,返回一个列表
    '''
    conn = sqlite3.connect(os.path.join(sys.path[0], "dy.db"))
    c = conn.cursor()
    c.execute('SELECT * FROM main.%s;' % (table_name))
    return c.fetchall()


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

# 获取视频无水印链接和文案(生产者)


def getVideo(url_queue: queue.Queue, video_queue: queue.Queue):
    '''
    获取视频无水印链接和文案(生产者)
    传入url队列和视频队列
    '''
    # 不断循环
    while True:
        share_url = url_queue.get()
        result = Dy().main(share_url)

        if result["status"] == 1:
            print("生产者线程%s出问题:" % (threading.current_thread().name), result)
            return

        video_url = result["data"]["video"]["video_url"]
        video_desc = result["data"]["video"]["desc"]
        video = (video_url, video_desc)
        # 添加元素到视频队列
        video_queue.put(video)
        print("生产者线程%s: 链接队列数量:%s 视频队列数量:%s" % (
            threading.current_thread().name, url_queue.qsize(), video_queue.qsize()))


def download_video(url_queue: queue.Queue, video_queue: queue.Queue, table_name):
    '''
    下载保存视频(消费者)
    '''
    # 不断循环
    while True:
        v_tuple = video_queue.get()
        url = v_tuple[0]
        desc = v_tuple[1]
        mkdirInPath(table_name)
        path = os.path.join(sys.path[0]+"//%s" % (table_name),
                            checkNameValid(desc)+".mp4")
        do_load_media(url, path)  # 下载视频
        print("消费者线程%s: 链接队列数量:%s 视频队列数量:%s" % (
            threading.current_thread().name, url_queue.qsize(), video_queue.qsize()))


if __name__ == "__main__":
    url_queue = queue.Queue()  # 链接队列
    video_queue = queue.Queue()  # 视频队列

    table_name = "common"

    for text, url in readSql(table_name):
        url_queue.put(url)

    # 创建获取链接线程
    for idx in range(64):
        t = threading.Thread(target=getVideo, args=(
            url_queue, video_queue), name=idx)
        t.start()

    # 创建下载视频线程
    for idx1 in range(256):
        t = threading.Thread(target=download_video, args=(
            url_queue, video_queue, table_name), name=idx1)
        t.start()
