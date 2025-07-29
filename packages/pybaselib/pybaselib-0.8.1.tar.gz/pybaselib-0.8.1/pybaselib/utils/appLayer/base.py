# -*- coding: utf-8 -*-
# @Author: maoyongfan
# @email: maoyongfan@163.com
# @Date: 2024/12/9 13:07

import os

def ping_ip(ip):
	res = os.system("ping {} -c 2".format(ip))
	return True if res == 0 else False

if __name__ == '__main__':
    # print(ping_ip('192.168.1.105'))
	print(ping_ip(1))