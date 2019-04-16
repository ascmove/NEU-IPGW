#!/usr/bin/python
# -*- coding:utf-8 -*-
# IP变动时发送邮件到指定邮箱
# 启动时发送邮件到指定邮箱
import os
import socket
import fcntl
import struct
import smtplib
from email.mime.text import MIMEText
import ConfigParser
import time

cf = ConfigParser.ConfigParser()
cf.read('/usr/local/neu/config.ini')

# 网卡名
eth_name = str(cf.get("eth", "eth_name"))
# 启动日志
boot_log = cf.get("boot", "boot_log")
# 启动标题
boot_email_title = cf.get("email", "boot_email_title")
# 日志路径
log_path = "/usr/local/neu/last_ip.log"

# 第三方 SMTP 服务
mail_host = str(cf.get("email", "mail_host"))  # SMTP服务器
mail_user = str(cf.get("email", "mail_user"))  # 用户名
mail_pass = str(cf.get("email", "mail_pass"))  # 登录密码
sender = str(cf.get("email", "sender"))  # 发件人邮箱
receivers = [str(cf.get("email", "receiver"))]  # 接收邮件
new_ip_email_title = str(cf.get("email", "new_ip_email_title"))


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def send_email(title, content):
    message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
    message['From'] = "{}".format(sender)
    message['To'] = ",".join(receivers)
    message['Subject'] = title

    smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
    smtpObj.login(mail_user, mail_pass)  # 登录验证
    smtpObj.sendmail(sender, receivers, message.as_string())  # 发送


def diff_last_ip(newip):
    with open(log_path, 'a+') as fp:
        fc = fp.read()
    if newip == fc:
        return False
    else:
        with open(log_path, 'w+') as fps:
            fps.write(newip)
            fps.close()
    return True


if __name__ == '__main__':
    upTime = os.popen('uptime -s').read().strip()
    upTimeStamp = int(time.mktime(time.strptime(upTime, "%Y-%m-%d %H:%M:%S")))
    with open(boot_log, 'a+') as bl:
        bt = bl.read()
    if len(bt) == 0:
        bt = 0
    if int(bt) != upTimeStamp:
        # 发现新的启动时间
        with open(boot_log, 'w+') as fw:
            fw.write(str(upTimeStamp))
        send_email(boot_email_title, 'Boot Time : '+upTime)
    ipaddr = str(get_ip_address(eth_name))
    if diff_last_ip(ipaddr):
        print('	New ip : ' + ipaddr)
        send_email(new_ip_email_title, ipaddr)
    else:
        print('Current ip : ' + ipaddr)
