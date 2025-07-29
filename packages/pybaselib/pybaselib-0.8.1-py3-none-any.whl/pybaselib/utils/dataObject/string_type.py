# -*- coding: utf-8 -*-
# @Author: maoyongfan
# @email: maoyongfan@163.com
# @Date: 2025/2/19 19:33
import json

def string_to_bytes_length(string: str) -> int:
    """
    字符串对应字节长度
    :param string:
    :return:
    """
    # byte = len(str(string.encode('utf-8').hex()))/2
    # print(byte)
    return len(string.encode('utf-8'))

def json_to_bytes_to_hex(data: dict) -> str:
    """
    json字符串转为字节再转为16进制
    :param string:
    :return:
    """
    json_str = json.dumps(data)
    byte_data = json_str.encode('utf-8')
    hex_str = byte_data.hex()
    return hex_str



if __name__ == "__main__":
    print(string_to_bytes_length("FFFFFF0700010000C0A8017A"))