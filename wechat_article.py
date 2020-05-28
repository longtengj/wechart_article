# -*- coding: utf-8 -*-

import os
import random
import re
import socket
import time
from time import sleep
from bs4 import BeautifulSoup
import requests
import json
import urllib.parse
from docx import Document
from docx.shared import Inches
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from math import ceil

from wechat_db import get_connect, sava_article

sess = requests.Session()

USER_AGENT = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
]
headers = {
    'Host': 'mp.weixin.qq.com',
    # 'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
    # 'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
    'User-Agent': random.choice(USER_AGENT),
    "Referer": "https://mp.weixin.qq.com/",
}

# socket.setdefaulttimeout(20)  # 设置socket层的超时时间为20秒

global rootpath  # 全局变量，存放路径
global time_gap  # 全局变量，每页爬取等待时间


def Login(username, pwd):
    browser = webdriver.Firefox()
    # browser = webdriver.Chrome()
    browser.maximize_window()
    browser.get(r'https://mp.weixin.qq.com')
    browser.implicitly_wait(60)
    account = browser.find_element_by_name("account")
    password = browser.find_element_by_name("password")
    if (username != "" and pwd != ""):
        account.click()
        account.send_keys(username)
        password.click()
        password.send_keys(pwd)
        # browser.find_element_by_xpath(r'//*[@id="header"]/div[2]/div/div/form/div[4]/a').click()
    # else:
    #     print("* 请在10分钟内手动完成登录 *")
    print("* 请在10分钟内手动完成登录 *")
    WebDriverWait(browser, 60 * 10, 0.5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, r'.weui-desktop-account__nickname'))
    )
    print("登陆成功")
    token = re.search(r'token=(.*)', browser.current_url).group(1)
    cookies = browser.get_cookies()
    with open("cookie.json", 'w+') as fp:
        fp.write(json.dumps(cookies))
        print(">> 本地保存cookie")
        fp.write(json.dumps([{"token": token}]))
        print(">> 本地保存token")
        fp.close()
    browser.close()
    print('token:', token)
    return token, cookies


def Add_Cookies(cookie):
    c = requests.cookies.RequestsCookieJar()
    for i in cookie:  # 添加cookie到CookieJar
        c.set(i["name"], i["value"])
        sess.cookies.update(c)  # 更新session里的cookie


def Get_WeChat_Subscription(token, query):
    if (query == ""):
        query = "autowalker"
    url = r'https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&token={0}&lang=zh_CN&f=json&ajax=1&random=0.5182749224035845&query={1}&begin=0&count=5'.format(
        token, query)
    html_json = sess.get(url, headers=headers).json()
    # print(html_json)
    fakeid = html_json['list'][0]['fakeid']
    nickname = html_json['list'][0]['nickname']
    print("fakeid:", fakeid)
    print("nickname: ", nickname)
    return fakeid, nickname


def Get_Articles(fakeid, nickname, range_dict):
    title_buf = []
    link_buf = []
    img_buf = []
    appmsgid_buf = []
    update_time_buf = []
    # 第一页计算总的分页数
    url = r'https://mp.weixin.qq.com/cgi-bin/appmsg?token={0}&lang=zh_CN&f=json&ajax=1&random={1}&action=list_ex&begin=0&count=5&query=&fakeid={2}&type=9'.format(
        token, random.random(), fakeid)
    html_json = sess.get(url, headers=headers).json()

    try:
        Total_Page = ceil(int(html_json['app_msg_cnt']) / 5)
    except Exception as e:
        print("!! 失败信息：", html_json['base_resp']['err_msg'])
        return
    print("总页数：", Total_Page)

    try:
        current_page = int(range_dict[nickname])
    except:
        current_page = 0
        range_dict[nickname] = 0
        with open(rootpath+"range.json", 'w+', encoding='UTF-8') as fp_range:
            json.dump(range_dict, fp_range, ensure_ascii=False)
            fp_range.close()

    for i in range(current_page, Total_Page):
        print("第[%d/%d]页" % (i + 1, Total_Page))
        begin = i * 5
        url = r'https://mp.weixin.qq.com/cgi-bin/appmsg?token={0}&lang=zh_CN&f=json&ajax=1&random={1}&action=list_ex&begin={2}&count=5&query=&fakeid={3}&type=9'.format(
            token, random.random(), begin, fakeid)
        html_json = sess.get(url, headers=headers).json()

        title_buf.clear()
        link_buf.clear()
        img_buf.clear()
        appmsgid_buf.clear()
        update_time_buf.clear()

        try:
            app_msg_list = html_json['app_msg_list']
        except:
            continue

        if (str(app_msg_list) == '[]'):
            break
        for j in range(20):
            try:
                title_buf.append(app_msg_list[j]['title'])
                link_buf.append(app_msg_list[j]['link'])
                img_buf.append(app_msg_list[j]['cover'])
                appmsgid_buf.append(str(app_msg_list[j]['appmsgid']))
                update_time_buf.append(str(app_msg_list[j]['update_time']))
                with open(rootpath + "/spider.txt", 'a+') as fp:
                    fp.write('*' * 60 + '\nMsgPage: ' + i + '\nMsgNumber: ' + j + '\nAppMsgId: ' + appmsgid_buf[
                        j] + '\nUpdateTime: ' + update_time_buf[j] +
                             '\nTitle: ' + title_buf[j] + '\nLink: ' + link_buf[j] + '\nImg: ' + img_buf[j] + '\r\n')
                    fp.close()
                    print(">> 第%d条写入完成：%s" % (j + 1, title_buf[j]))
            except Exception as e:
                # print(">> 本页抓取结束")
                # print(e)
                break
        print(">> 一页抓取结束，开始下载")
        get_content(title_buf, link_buf, appmsgid_buf, update_time_buf, app_msg_list)
        print(">> 休息 %d s" % time_gap)
        sleep(time_gap)
        # 修改页，断点续传
        range_dict[nickname] = i + 1
        with open(rootpath+"range.json", 'w+', encoding='UTF-8') as fp_range_dict:
            json.dump(range_dict, fp_range_dict, ensure_ascii=False)
            fp_range_dict.close()
    print(">> 抓取结束")


def get_content(title_buf, link_buf, appmsgid_buf, update_time_buf, app_msg_list):  # 获取地址对应的文章内容
    each_title = ""  # 初始化
    each_url = ""  # 初始化
    length = len(title_buf)

    for index in range(length):
        try:
            each_title = re.sub(r'[\|\/\<\>\:\*\?\\\"]', "_", title_buf[index])  # 剔除不合法字符
            filepath = rootpath + "/" + appmsgid_buf[index] + "_" + each_title  # 为每篇文章创建文件夹
            if (not os.path.exists(filepath)):  # 若不存在，则创建文件夹
                os.makedirs(filepath)
            os.chdir(filepath)  # 切换至文件夹

            html = sess.get(link_buf[index], headers=headers)
            soup = BeautifulSoup(html.text, 'lxml')
        except Exception as e:
            print(e)
        # 1 保存文件到word
        # currentDocument =Document(each_title)
        # 文章标题
        # currentDocument.add_Heading()
        sleep(1)
        # 2 保存到txt
        try:
            rich_media_content = soup.find(class_="rich_media_content")
            if not rich_media_content:
                continue;
            article = rich_media_content.find_all("p")  # 查找文章内容位置
            img_urls = rich_media_content.find_all("img")  # 获得文章图片URL集

            print("*" * 60)
            print(each_title)
            print(">> 保存文档 - ", end="")
            article_context = []
            article_context.clear()
            for i in article:
                line_content = i.get_text()  # 获取标签内的文本
                # print(line_content)
                if (line_content != None):  # 文本不为空
                    article_context.append(line_content)
                    with open(each_title + r'.txt', 'a+', encoding='utf-8') as fp_article_context:
                        fp_article_context.write(line_content + "\n")  # 写入本地文件
                        fp_article_context.close()
            # print("完毕!")

            print(">> 保存图片 - %d张" % len(img_urls), end="")
            img_uris = []
            img_uris.clear()
            for i in range(len(img_urls)):
                try:
                    img_uris.append(str(img_urls[i]["data-src"]))
                    img_uris.append(",")
                    pic_down = requests.get(img_urls[i]["data-src"])
                    with open(str(i) + r'.jpeg', 'ab+') as fp_pic_down:
                        fp_pic_down.write(pic_down.content)
                        fp_pic_down.close()
                    sleep(1)
                    if i >= 20:
                        break
                except:
                    img_uris.append(str(img_urls[i]["src"]))
                    img_uris.append(",")
                    pic_down = requests.get(img_urls[i]["src"])
                    with open(str(i) + r'.jpeg', 'ab+') as fp_pic_down:
                        fp_pic_down.write(pic_down.content)
                        fp_pic_down.close()
                    sleep(1)
                    if i >= 20:
                        break
        except Exception as e:
            print(e)
        # 保存 app_msg_list 以json格式到数据库 dumps是将dict转化成str格式，loads是将str转化成dict格式
        # 3 保存到mysql
        sava_article(query_name, each_title, "".join(img_uris), str(article_context), str(app_msg_list[index]),
                     int(update_time_buf[index]));

        sleep(1)

    print("完毕!\r\n")


if __name__ == '__main__':
    print("*" * 100)
    print("* 程序原理:")
    print(">> 通过selenium登录获取token和cookie，再自动爬取和下载")
    print("* 使用前提： *")
    print(">> 电脑已装Firefox、Chrome、Opera、Edge等浏览器")
    print(">> 下载selenium驱动放入python安装目录，将目录添加至环境变量(https://www.seleniumhq.org/download/)")
    print(">> 申请一个微信公众号(https://mp.weixin.qq.com)")
    print("*" * 100)
    print("\r")
    # get_connect()
    # query_name = input("输入公众号的英文名称，为空则默认数字化说(autowalker)：\n>> ")
    query_names = ["罗氏诊断DiaLog", "日立诊断", "雅培诊断远程支持中心", "迈瑞客服服务中心", "贝克曼库尔特临床诊断"]
    # query_names = ["雅培诊断远程支持中心", "迈瑞客服服务中心"]
    print("* 下面将输入自己公众号的账号密码(获取token和cookie)，为空则自动打开页面后手动输入 *")
    username = input("账号：")
    # username = "@qq.com"
    # pwd = input("密码：")
    # time_gap = input("输入每页爬取等待时间(一页约10条，越短越快被限制)，为空则默认为10s：\n>> ")
    time_gap = input("输入每页爬取等待时间(一页约10条，越短越快被限制)，为空则默认为10s：\n>> ")
    time_gap = 8
    if (time_gap == ""):
        time_gap = 10
    else:
        time_gap = int(time_gap)
    token = '1819535186'
    cookies = json.loads(
        r'[{"secure":true,"expiry":2147483647,"value":"L9Vua8LcrI8Y7xHJAAAAAKFjHBIybgPYQ7SD5rvW1n4=","path":"/","name":"ua_id","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":false,"expiry":2147385600,"value":"4625682432","path":"/","name":"pgv_pvi","httpOnly":false,"domain":".qq.com"},{"secure":false,"value":"s2843642880","path":"/","name":"pgv_si","httpOnly":false,"domain":".qq.com"},{"secure":true,"value":"36698d9ca15ec90e3e70dd84de82e7d2","path":"/","name":"uuid","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"value":"0993b4a3856eb1098137e17feea4b9bb4a882d25","path":"/","name":"ticket","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"value":"gh_265b7e02288e","path":"/","name":"ticket_id","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"value":"FMQfNtHCWCVa2Ty00P1y0P0oqBqL0mY0","path":"/","name":"cert","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":false,"expiry":1589708469,"value":"1","path":"/","name":"noticeLoginFlag","httpOnly":false,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462080,"value":"3017773126","path":"/","name":"data_bizuin","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462080,"value":"kwVo6eCekaCz27dZ75EZgVch0g3HzV3kk536UoEZRIdPApBa/xCzYpIy6R717qq4","path":"/","name":"data_ticket","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":2147483647,"value":"","path":"/","name":"xid","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1589794880,"value":"DbBh56bHNFjFVlULO2utB430jOSGl6ewu7fFW1l5m5E=","path":"/","name":"openid2ticket_oRpDfs6J-Dndsh-ZOl6ItUFxJVac","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":4294967295,"value":"zh_CN","path":"/","name":"mm_lang","httpOnly":false,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462081,"value":"gh_265b7e02288e","path":"/","name":"slave_user","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462081,"value":"VkxCV2xzanM5bHpvM212UnFBM2RCNEsyTEc1aXNyMHdhY0xqSXBGTkpIcW1pdXhqMHo2U1NTUnNWdHR5MEhYbjJTZUdnR2hEOVBTcXNWUUM5MHdTVGlIRlliSnUwdWRXYnJuSmRZc0QwbWVRNHhlYzNKU3Y4Q0ZTMmZPd0F6UDBvcW53WllPc0dUNlVZTGlh","path":"/","name":"slave_sid","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462081,"value":"3298609352","path":"/","name":"bizuin","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462081,"value":"3298609352","path":"/","name":"slave_bizuin","httpOnly":true,"domain":"mp.weixin.qq.com"},{"secure":true,"expiry":1587462081,"value":"CAESIDQXWx03rBKocl90QpQ9wnNhUFLtPoKtdqb3xYAEG27c","path":"/","name":"rand_info","httpOnly":true,"domain":"mp.weixin.qq.com"}]')
    [token, cookies] = Login(username, pwd)
    Add_Cookies(cookies)
    range_dict = {}
    current_cwd = os.getcwd() + r"/spider/"
    for query_name in query_names:
        [fakeid, nickname] = Get_WeChat_Subscription(token, query_name)
        rootpath = current_cwd + nickname

        # 断点续传
        try:
            with open(rootpath+"range.json", 'r+', encoding='UTF-8') as fp:
                range_dict = json.load(fp)
                print("断点续传页数：", str(range_dict))
                fp.close()
        except:
            pass

        # range_dict[query_name] = 176
        # with open("range.json", 'w+') as fp_range_dict:
        #     json.dump(range_dict, fp_range_dict)
        #     fp_range_dict.close()

        # Get_Articles(0, query_name, range_dict)
        Get_Articles(fakeid, query_name, range_dict)
