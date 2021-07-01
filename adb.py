'''`
Author: whalefall
Date: 2021-06-29 18:04:27
LastEditTime: 2021-06-30 16:11:03
Description: 抖音adb
'''
import os
import sqlite3
from time import sleep
import subprocess
import re
import sys 
import requests
import aiohttp
import aiofiles
import asyncio

# 获取剪切板内容


def getCopy() -> tuple:
    try:
        c = subprocess.check_output(
            'adb shell am broadcast -a clipper.get').decode()
        # print(c)
        if "found" in c:
            print("手机连接掉线!")
            sys.exit()
        pat = re.compile(r"[a-zA-z]+://[^\s]*")
        url = pat.findall(c)[0]
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
    conn = sqlite3.connect("dy.db")
    c = conn.cursor()

    # 新建表
    c.execute('''create table if not exists `{}` (
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


# 利用个人搭建的API下载.
def download_videofile(video_link, file_name):
    file_name = checkNameValid(file_name)
    # file_name = link.split('/')[-1]
    # print("文件下载:%s" % file_name)
    r = requests.get(video_link, stream=True).iter_content(
        chunk_size=1024 * 1024)
    with open(os.path.join(sys.path[0]+"\\qinlanlan", "%s.mp4" % (file_name)), 'wb') as f:
        for chunk in r:
            if chunk:
                f.write(chunk)

    print("[下载完成!]%s.mp4" % file_name)

    return


def DownloadVidoe(url, text):
    header = {
        "User-Agent": "Mozilla/5.0 (Linux; U; Android 8.1.0; zh-cn; BLA-AL00 Build/HUAWEIBLA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/8.9 Mobile Safari/537.36",
    }
    api = "http://192.168.101.4:5000/dy/?url=%s" % (url)
    resp = requests.get(api).json()
    url = resp.get('video_url')
    title = resp.get('title')
    # 如果文案为空就取分享连接的文字
    if title == "":
        title = text

    if url == "0":
        print("视频解析出现错误!")
        return None
    download_videofile(url, title)


# 检查文件名
def checkNameValid(name=None):
    """
    检测Windows文件名称！
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

# 若检测到有多次重复的情况 -> 即 点击失误/加载过长/剪切板服务挂了 重新打开app


def restartDyApp():

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


if __name__ == "__main__":
    # 数据重复计数器
    count = 0
    while True:

        # 点击分享按钮
        os.system("adb shell input tap 998 1296")
        sleep(0.2)
        # 点击复制链接按钮
        os.system("adb shell input tap 154 1492")
        # sleep(0.2)
        # 获取剪切板
        text, url = getCopy()
        sql_result = writeSQL(Text=text, Url=url)

        # try:
        #     DownloadVidoe(url, text)
        # except Exception as e:
        #     print("视频下载出错:%s" % (e))

        if count >= 3:
            print("数据已重复三次,准备重启 抖音APP")
            restartDyApp()
            # 还原计数器
            count = 0

        if sql_result == "0":
            count += 1
            print("数据重复第%s次数" % (count))

        # 下滑
        os.system("adb shell input swipe 520 1400 536 599")
