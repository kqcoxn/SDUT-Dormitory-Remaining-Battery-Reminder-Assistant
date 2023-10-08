from enum import Enum
import urllib3
import requests
from bs4 import BeautifulSoup
import re
import json
import os

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 查询类型枚举
class Power_Type(Enum):
    SOCKET = 1
    AC = 2


# 错误值枚举
class Error_Type(Enum):
    NETWORK_ERROR = -1
    PARAM_ERROR = -2
    OTHER_ERROR = -999


# json读取
def get_data(file_name: str) -> dict:
    # 获取文件路径
    current_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(
        current_directory, 'data', file_name + '.json')

    # 读取JSON文件
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)
        return data


# 获取电量
def obtain_power(power_type: Power_Type) -> float:
    # 构造请求
    url = "https://hqfw.sdut.edu.cn/stu_elc.aspx"
    headers = get_data("Headers")
    data = get_data(
        "Socket") if power_type == Power_Type.SOCKET else get_data("AC")

    # 请求数据
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
    except Exception:
        return -1

    # 数据处理
    soup = BeautifulSoup(response.text, "html.parser")
    span_tag = soup.find("span", {"id": "lblyue"})
    html_text = span_tag.text
    power = re.search(r'\d+\.\d+', html_text).group()
    try:
        return float(power)
    except Exception:
        return -2


socket_power = obtain_power(Power_Type.SOCKET)
ac_power = obtain_power(Power_Type.AC)

print(socket_power, ac_power)
