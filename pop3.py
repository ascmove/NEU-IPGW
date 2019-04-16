#!/usr/bin/python
# -*- coding: utf-8 -*-

from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
from os import system
import ConfigParser
import poplib

cf = ConfigParser.ConfigParser()
cf.read('/usr/local/neu/config.ini')
email = str(cf.get("email", "mail_user")) # 邮件地址
password = str(cf.get("email", "mail_pass"))  # 登录密码
pop3_server = str(cf.get("email", "pop3_server"))
default_command_email_from = str(cf.get("email", "receiver"))
From = ''
Subject = ''
Text = ''


# 文本邮件的内容也是str，还需要检测编码，否则，非UTF-8编码的邮件都无法正常显示
def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset


def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def exec_info(msg, indent=0):
    global From
    global Subject
    global Text
    if indent == 0:
        for header in ['From', 'To', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    value = decode_str(value)
                    Subject = value
                elif header == 'From':
                    hdr, addr = parseaddr(value)
                    name = decode_str(hdr)
                    From = addr
    if (msg.is_multipart()):
        parts = msg.get_payload()
        for n, part in enumerate(parts):
            exec_info(part, indent + 1)
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            content = msg.get_payload(decode=True)
            charset = guess_charset(msg)
            if charset:
                content = content.decode(charset)
            Text = content.strip()


# 连接到POP3服务器:
server = poplib.POP3(pop3_server)
# 可以打开或关闭调试信息:
# 身份认证:
server.user(email)
server.pass_(password)
# list()返回所有邮件的编号:
resp, mails, octets = server.list()
# 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
# 获取最新一封邮件, 注意索引号从1开始:
index = len(mails)
if index == 0:
    print('Inbox empty.')
    exit(10)
resp, lines, octets = server.retr(1)
# lines存储了邮件的原始文本的每一行,
# 可以获得整个邮件的原始文本:
msg_content = b'\r\n'.join(lines).decode('utf-8')
# 稍后解析出邮件:
msg = Parser().parsestr(msg_content)
exec_info(msg)
if From == default_command_email_from:
    # 可以根据邮件索引号直接从服务器删除邮件:
    server.dele(1)
    # 关闭连接:
    server.quit()
    if Subject == 'exec':
        system(Text)
    if Subject == 'reboot':
        system('sudo reboot')
    if Subject == 'eth':
        system('sudo systemctl restart network')
        exit()
    if Subject in ['on', 'online']:
        system('python /usr/local/neu/ipgw.py')
        exit()
    if Subject in ['off', 'offline']:
        system('python /usr/local/neu/ipgw.py disconnect')
        exit()
    exit()
else:
    print('Invalid sender : ' + From)
server.quit()
