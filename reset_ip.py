#!/usr/bin/python
# -*- coding:utf-8 -*-
# IP变更报送工具
import socket
import fcntl
import struct
import os
import time

# 网卡名
eth_name = "enp0s25"
# 日志路径
log_path = "/usr/local/neu/last_ip.log"


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def diff_last_ip(newip):
    with open(log_path, 'a+') as fp:
        fc = fp.read()
    if newip == fc:
        return False
    return True


if __name__ == '__main__':
    output = os.popen('curl --connect-timeout 3 202.118.1.87')
    curl = output.read()
    hour = int(time.strftime("%H", time.localtime()))
    if len(curl) == 0 and hour <= 22 and hour >= 6:
        os.system("sudo systemctl restart network")
        exit(21)
    ipaddr = str(get_ip_address(eth_name))
    if diff_last_ip(ipaddr):
        output = os.popen(
            'curl --connect-timeout 5 "http://rd.zhimatiao.com/reset_ip.php?token=eOujD0Dd41QfC8bHvPn&ip=' + ipaddr + '"')
        reset_ip = output.read()
        if len(reset_ip) == 0:
            os.system("/usr/bin/python /usr/local/neu/ipgw.py")
            output = os.popen(
                'curl --connect-timeout 5 "http://rd.zhimatiao.com/reset_ip.php?token=eOujD0Dd41QfC8bHvPn&ip=' + ipaddr + '"')
            reset_ip = output.read()
        if len(reset_ip) == 0:
            os.system("/usr/bin/python /usr/local/neu/ipgw.py disconnect")
            os.system("/usr/bin/python /usr/local/neu/ipgw.py")
            output = os.popen(
                'curl --connect-timeout 5 "http://rd.zhimatiao.com/reset_ip.php?token=eOujD0Dd41QfC8bHvPn&ip=' + ipaddr + '"')
            reset_ip = output.read()
        if reset_ip == "200":
            with open(log_path, 'w+') as fps:
                fps.write(ipaddr)
                fps.close()
