#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-03 13:45:27
LastEditTime: 2021-07-04 12:14:50
Description: 抖音去水印函数文件
'''
import re
import requests
import random


class Dy(object):
    def __init__(self) -> None:
        '''
        初始化函数,要求UA必须是手机的
        '''
        self.UAlist = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366 MicroMessenger/6.7.3(0x16070321) NetType/WIFI Language/zh_CN",
            "Mozilla/5.0 (Linux; U; Android 8.0.0; zh-CN; MHA-AL00 Build/HUAWEIMHA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/12.1.4.994 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; U; Android 8.0.0; zh-cn; Mi Note 2 Build/OPR1.170623.032) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.128 Mobile Safari/537.36 XiaoMi/MiuiBrowser/10.1.8",
        ]

    def get_video_id(self, content: str) -> str:
        '''
        传入任意内容,匹配单个链接,并访问该链接.
        返回获取的视频id
        '''
        try:
            pat_url = re.compile(r"[a-zA-z]+://[^\s]*")
            url = pat_url.findall(content)[0]

            full_url = requests.get(
                url, headers={"User-Agent": random.choice(self.UAlist)}).url
            video_id = re.findall('video/(\d+)/', str(full_url))[0]
        except Exception as e:
            print("[API]抖音解析错误:%s" % (e))
            return None
        else:
            return video_id

    def get_video_all(self, video_id) -> dict:
        '''
        传入视频id,访问抖音官方api,以字典的形式返回视频详细信息.(视频信息&作者信息)
        '''
        if video_id == None:
            return {"status": 1, "why": "视频id获取出错,请检查传入的内容!"}

        api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
        api_resp = requests.get(
            api_url, headers={"User-Agent": random.choice(self.UAlist)}).json()

        # print(api_resp)
        if api_resp["item_list"] == []:
            return {"status": 1, "why": "抖音官方无水印api出现问题"}

        # 视频信息
        try:
            video = {}
            video["desc"] = api_resp["item_list"][0]["desc"]  # 视频文案
            # 视频封面图
            video["video_pic"] = api_resp["item_list"][0]["video"]["cover"]["url_list"][0]
            # 视频无水印链接(需要用手机UA访问)
            video["video_url"] = api_resp["item_list"][0]["video"]["play_addr"]["url_list"][0].replace(
                "wm", "")
            # 如需获取视频重定向后的链接请开启这个(可能会造成解析速度下降)
            # video["video_url"] = requests.get(
            #     url, headers={"User-Agent": random.choice(self.UAlist)}).url

            video["video_mp3"] = api_resp["item_list"][0]["music"]["play_url"]["url_list"][0]

            # 作者信息
            author = {}
            author["name"] = api_resp["item_list"][0]["author"]["nickname"]
            author["avatar"] = api_resp["item_list"][0]["author"]["avatar_larger"]["url_list"][0]
            author["sign"] = api_resp["item_list"][0]["author"]["signature"]

            datas = {"video": video, "author": author}

            return {"status": 0, "data": datas}
        except Exception as e:
            with open("dy.log", "a") as f:
                f.write("id:%s 错误:%s 原始数据:%s \n" %
                        (str(video_id), str(e), str(api_resp)))

    # 主运行
    def main(self, content) -> dict:
        video_id = self.get_video_id(content)
        # print(video_id)
        video_dict = self.get_video_all(video_id)
        # print(video_dict)
        return video_dict


if __name__ == "__main__":
    c = Dy().main("https://www.iesdouyin.com/share/video/6945026162334747935/?region=CN&mid=6945026229363919629&u_code=9a2ec96cgag&titleType=title&did=MS4wLjABAAAAZXSzY2fm0jSkL5eTKW0M5AJGcb0uGkLBG45HR7COt-4&iid=MS4wLjABAAAArjb9wJnom7THYHT-lP5KHqun-MS1ROtNMJdjLaogrmo&with_sec_did=1&utm_source=copy_link&utm_campaign=client_share&utm_medium=android&app=aweme&iid=651361055932990&timestamp=1624970564")
    print(c)
