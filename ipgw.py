#!/usr/bin/python
# -*- coding:utf-8 -*-
# 通用网关认证工具
import datetime
import time
import ConfigParser
import sys
import json
import random
import smtplib
import urllib
import urllib2
from email.mime.text import MIMEText

cf = ConfigParser.ConfigParser()
cf.read('/usr/local/neu/config.ini')
access_forbidden_file = str(cf.get("access", "access_forbidden_file"))  # SMTP服务器

# 第三方 SMTP 服务
mail_host = str(cf.get("email", "mail_host"))  # SMTP服务器
mail_user = str(cf.get("email", "mail_user"))  # 用户名
mail_pass = str(cf.get("email", "mail_pass"))  # 登录密码
sender = str(cf.get("email", "sender"))  # 发件人邮箱
receivers = [str(cf.get("email", "receiver"))]  # 接收邮件

ipgw_account = str(cf.get("ipgw", "ipgw_account"))  # 网关账号
ipgw_passwd = str(cf.get("ipgw", "ipgw_passwd"))  # 网关密码

srun_portal_pc_url = str(cf.get("ipgw", "srun_portal_pc_url"))  # 认证地址
auth_action_url = str(cf.get("ipgw", "auth_action_url"))  # 在线信息
test_connection_url = str(cf.get("ipgw", "test_connection_url"))  # 测试联网链接


def auth_portal_login(username, password):
    with open(access_forbidden_file, 'a+') as fp:
        fc = fp.read()
    if len(fc) == 0:
        fc = 0
    if int(fc) > int(time.time()):
        return ['access_forbidden']
    test_data = {'action': 'login', 'user_ip': '', 'nas_ip': '', 'user_mac': '', 'url': '', 'username': username,
                 'password': password}
    test_data_urlencode = urllib.urlencode(test_data)
    requrl = srun_portal_pc_url
    req = urllib2.Request(url=requrl, data=test_data_urlencode)
    res_data = urllib2.urlopen(req)
    res = res_data.read()

    if "网络已连接" in res:
        get_online_info()
        return ['ok']
    elif "5分钟" in res:
        with open(access_forbidden_file, 'w+') as fw:
            fw.write(str(int(time.time()+300)))
        return ['access_forbidden']
    else:
        return ['failed']


def get_online_info():
    k = int(random.random() * 100000)
    test_data = {'action': 'get_online_info', 'k': k}
    test_data_urlencode = urllib.urlencode(test_data)
    requrl = auth_action_url
    req = urllib2.Request(url=requrl, data=test_data_urlencode)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return res.split(',')


def connection_test():
    test_data = {'action': 'connect'}
    test_data_urlencode = urllib.urlencode(test_data)
    requrl = test_connection_url
    req = urllib2.Request(url=requrl, data=test_data_urlencode)
    res_data = urllib2.urlopen(req)
    return res_data.read()


def auth_portal_logout(username, password):
    test_data = {'action': 'logout', 'ajax': 1, 'username': username, 'password': password}
    test_data_urlencode = urllib.urlencode(test_data)
    requrl = auth_action_url
    req = urllib2.Request(url=requrl, data=test_data_urlencode)
    res_data = urllib2.urlopen(req)
    res = res_data.read()


def send_email(title, content):
    message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
    message['From'] = "{}".format(sender)
    message['To'] = ",".join(receivers)
    message['Subject'] = title

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
        smtpObj.login(mail_user, mail_pass)  # 登录验证
        smtpObj.sendmail(sender, receivers, message.as_string())  # 发送
    except smtplib.SMTPException as e:
        print(e)


def mail_content_builder(res):
    giga = round(float(res[0]) / 1000 / 1000 / 1000, 2)
    return "已用流量：" + str(giga) + "GB\r\n帐户余额：" + res[2]


def try_notify(res):
    with open('/usr/local/neu/auth.log', 'a+') as fp:
        fc = fp.read()
    with open('/usr/local/neu/auth.log', 'w+') as fps:
        now_time = str(datetime.datetime.now())
        if len(fc) == 0:
            send_email(res[5], mail_content_builder(res))
        else:
            log = json.loads(fc)
            if log['ip'] != res[5]:
                send_email(res[5], mail_content_builder(res))
        res_dict = {"flow": res[0], "online": res[1], "ip": res[5], "update": now_time}
        string = json.dumps(res_dict)
        fps.write(string)
        fps.close()


if __name__ == '__main__':

    # 自动登录设置True 命令行手动认证设置False
    auth_auto = False

    if auth_auto:
        online_info = get_online_info()
        if online_info[0] == 'not_online':
            # 本机未在线，进行登入程序
            res = auth_portal_login(ipgw_account, ipgw_passwd)
            if res[0] != 'failed':
                try_notify(res)
        else:
            try:
                connection = connection_test()
                res = get_online_info()
                try_notify(res)
            except urllib2.URLError as e:
                wk = int(time.strftime("%w", time.localtime()))
                if 1 <= wk and 5 >= wk:
                    auth_portal_logout(ipgw_account, ipgw_passwd)
                    res = auth_portal_login(ipgw_account, ipgw_passwd)
                    try_notify(res)
    else:
        if len(sys.argv) == 1:
            online_info = get_online_info()
            if online_info[0] == 'not_online':
                # 本机未在线，进行登入程序
                res = auth_portal_login(ipgw_account, ipgw_passwd)
                # print(res)
                if res == None or res[0] == 'access_forbidden':
                    print "网关繁忙，请等待5分钟再试"
                elif res == None or res[0] == 'ok':
                    print "认证成功"
                else:
                    print "认证失败(202)"
            else:
                print "已在线"
        elif len(sys.argv) == 2 and sys.argv[1] == "disconnect":
            online_info = get_online_info()
            if online_info[0] == 'not_online':
                print "未上线"
            else:
                auth_portal_logout(ipgw_account, ipgw_passwd)
                print "已下线"
        else:
            print "Use [ipgw.py disconnect] to disconnet from server."
