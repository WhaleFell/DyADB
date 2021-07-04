<!--
 * @Author: whalefall
 * @Date: 2021-07-02 04:08:20
 * @LastEditTime: 2021-07-04 11:17:53
 * @Description: 
-->
# ADB 抖音自动刷程序
## 利用 Python 驱动 ADB 实现在 Android 设备上自动刷抖音.
## 并把刷到的视频链接复制下来,提取文本与链接,自动存入 `Sqlite` 数据库.
## 根据自己搭建的接口(详见:[PythonAPI](https://github.com/AdminWhaleFall/PythonAPI)),获取无水印链接并下载.
# ToDo
- [X] 1. 增加多线程(或者异步下载)批量下载视频.
  > 注意: 当下载过快时,会出现`'content_length'` 错误,系抖音官方**反扒**所导致,可以自己设置线程池并发数 `max_working`
- [ ] 2. 将视频文案绘制**词云图**,并分析文案词频.
- [X] 3. 寻找到更好的**去水印方法**,不依赖于搭建的API.
  > 找到一个利用手机网页的解析api,**目测没有限制**