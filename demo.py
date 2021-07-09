#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-09 18:19:14
LastEditTime: 2021-07-09 18:24:02
Description: 草稿
'''
import os
from time import sleep

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

if __name__=="__main__":
    # restartDyApp()
    os.system("adb shell input tap 548 1860")