from nonebot import get_driver, on_command, require, get_bots
from nonebot.rule import to_me
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from .config import Config
from enum import Enum
import urllib3
import requests
from bs4 import BeautifulSoup
import re
import datetime

# 加载配置
global_config = get_driver().config
config = Config.parse_obj(global_config)

# 引入依赖
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

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


# 读取参数
def get_webforms_data(power_type: Power_Type) -> dict:
    obj = {}

    if power_type == Power_Type.SOCKET:
        obj = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": "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",
            "__VIEWSTATEGENERATOR": "69E791B9",
            "__EVENTVALIDATION": "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",
            "RadioButtonList2": "",
            "RadioButtonList1": "西校区",
            "DropDownList1": "310",
            "DropDownList2": "5",
            "DropDownList3": "5251",
            "btn_submit": "查 询"
        }
    elif power_type == Power_Type.AC:
        obj = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': '/wEPDwUJNTY5MzI0NjQ5D2QWAgIDD2QWEgIBDxBkZBYBAgFkAgMPEGRkFgFmZAIFDxAPFgYeDURhdGFUZXh0RmllbGQFB2xvdWRvbmceDkRhdGFWYWx1ZUZpZWxkBQJpZB4LXyFEYXRhQm91bmRnZBAVGg4xI+WFrOWvk+WNl+alvA4xI+WFrOWvk+WMl+alvAgyI+WFrOWvkwgzI+WFrOWvkwg0I+WFrOWvkwg1I+WFrOWvkwg2I+WFrOWvkwg3I+WFrOWvkwg4I+WFrOWvkwg5I+WFrOWvkwkxMCPlhazlr5MJMTEj5YWs5a+TCTEyI+WFrOWvkw8xMyPlhazlr5PljZfmpbwPMTMj5YWs5a+T5YyX5qW8CTE0I+WFrOWvkwkxNSPlhazlr5MJMTYj5YWs5a+TCTE3I+WFrOWvkwkxOCPlhazlr5MJMTkj5YWs5a+TCTIwI+WFrOWvkwkyMSPlhazlr5MJMjIj5YWs5a+TDOeglOWNl+WFrOWvkwznoJTljJflhazlr5MVGgQzMTEwBDMxMTEEMzEyMAQzMTMwBDMxNDAEMzE1MAQzMTU2BDMxNTkEMzE2NgQzMTY4BDMxNzAEMzE3MQQzMTcyBDMxNzQEMzE3NQQzMTc2BDMxNzgEMzE4MAQzMTgyBDMxODQEMzE4NgQzMTg4BDMxOTAEMzE5MgQzMTk2BDMxOTcUKwMaZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2cWAQIGZAIHDxAPFgIfAmdkEBUGATEBMgEzATQBNQE2FQYBMQEyATMBNAE1ATYUKwMGZ2dnZ2dnFgECBGQCCQ8QDxYGHwAFBHJvb20fAQUHcm9vbV9pZB8CZ2QQFSoOWDYtNTAx56m66LCDICAOWDYtNTAy56m66LCDICAOWDYtNTAz56m66LCDICAOWDYtNTA056m66LCDICAOWDYtNTA156m66LCDICAOWDYtNTA256m66LCDICAOWDYtNTA356m66LCDICAOWDYtNTA456m66LCDICAOWDYtNTA556m66LCDICAOWDYtNTEw56m66LCDICAOWDYtNTEx56m66LCDICAOWDYtNTEy56m66LCDICAOWDYtNTEz56m66LCDICAOWDYtNTE056m66LCDICAOWDYtNTE156m66LCDICAOWDYtNTE256m66LCDICAOWDYtNTE356m66LCDICAOWDYtNTE456m66LCDICAOWDYtNTE556m66LCDICAOWDYtNTIw56m66LCDICAOWDYtNTIx56m66LCDICAOWDYtNTIy56m66LCDICAOWDYtNTIz56m66LCDICAOWDYtNTI056m66LCDICAOWDYtNTI156m66LCDICAOWDYtNTI256m66LCDICAOWDYtNTI356m66LCDICAOWDYtNTI456m66LCDICAOWDYtNTI556m66LCDICAOWDYtNTMw56m66LCDICAOWDYtNTMx56m66LCDICAOWDYtNTMy56m66LCDICAOWDYtNTMz56m66LCDICAOWDYtNTM056m66LCDICAOWDYtNTM156m66LCDICAOWDYtNTM256m66LCDICAOWDYtNTM356m66LCDICAOWDYtNTM456m66LCDICAOWDYtNTM556m66LCDICAOWDYtNTQx56m66LCDICAOWDYtNTQz56m66LCDICAOWDYtNTQ156m66LCDICAVKgUxODg1OQUxODg2MAUxODg2MQUxODg2MgUxODg2MwUxODg2NAUxODg2NQUxODg2NgUxODg2NwUxODg2OAUxODg2OQUxODg3MAUxODg3MQUxODg3MgUxODg3MwUxODg3NAUxODg3NQUxODg3NgUxODg3NwUxODg3OAUxODg3OQUxODg4MAUxODg4MQUxODg4MgUxODg4MwUxODg4NAUxODg4NQUxODg4NgUxODg4NwUxODg4OAUxODg4OQUxODg5MAUxODg5MQUxODg5MgUxODg5MwUxODg5NAUxODg5NQUxODg5NgUxODg5NwUxODg5OAUxODg5OQUxODkwMBQrAypnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dkZAIPDw8WAh4EVGV4dAUDWDYtZGQCEQ8PFgIfAwUCMzBkZAITDw8WAh8DBQI2M2RkAhUPDxYCHwMFFeilv+agoeWMuuepuuiwg+eUqOeUtWRkZHVDMfkx9LNkGiea97lCSOqIx0iuR9EsGryXoiNU2zBE',
            '__VIEWSTATEGENERATOR': '69E791B9',
            '__EVENTVALIDATION': '/wEdAFOvkrbVJqFnExSAyOK9NA1WXEA1jHRzrDRWK42UTH4/oy818b5wYcyI0+/7m77mzsML5ZEnI492nrEFT7NfyiCNmonnH2CbSvxHeJjL5BDlVZYQJk9BEu6uNMVVQ9NYQ1YYkUoauLGE1EgGQoeJN5uYqwBRwVCDJK36KsHLRDQyVwB9+DvjtCj6gqlXl2y5ax81aSmn6R9vXHPbYZy/xSiw1Lb00WwTPBoNRpfc3Pu4+LBNzVHHbAJU63g6iN1BnEWu8t3+b9bVRvGaiFHwCxF6jJY6fs6ZkzUCoousOjkRw9jQdu83bROovT4g9kvS9ML74cygaQU7J+I6tIUKmVkGIU/z/LGxdWQr6K3CQDHZXMJLmT18ZcN0Sfq0zYoIne6M6l7VO7BjCzpyTJxLvMpo++KvchuO9J+MBZHVrmbQ5o+jOjHtZxVl+pjTBmsmjBHva3gnMRmovOG+RXB8RG+EAeTh6zJSqiGSjuS6MUkix5KXMcM3PUn19bAO+Hvte8nTbUBZXk0EKoQpM0/hj1uAJ3b5fPyhHx1zn4A61fXMLACpbw/0kPY0aA4wt4uGSm9jGJLQncP4tBTXsy/6579daWRpE3j656CV2KqddvpJxwALfDP/bgo9Qya+CLbrZXOf5qMRXs/M7FjMWV7ZPtSxsMhp/Wj26ilTyuYs4p1Zdu/o7RWpheKX3HHCMao04krRPHjzN2L6dQ5B5/wdZ4pdKn3cDZE+AWbDtjM4OcWriznFwdzO0FqKaivXwoQ+bsNkqdegLuwCZAJdKSH91CcvriEBKDD5mjrHHTPmmm6pVzoL3xVCNTvzUGc7nUyBLXBMRdh9/s61rsnrSB3YDaxYPRcOLk5iA7U5jdY6ysjjCX/Jo1C9aZIVPVp4NLgpraka98GJv/V9mLhQPJGly8huaJ0zqfHxrzAvcpu9/ihMv1vVvlAWjTym4D4jE+CXNwtrKQSaaXUaXeGoddOF/3E+mSzJjAP0tD8nIySV+9ncFjK4Hvwwie75SsckulXTWoImHtw4rU6Zn4fsloS7lKktt5t0m1ss6nBHUY9MNUmifw6TL9XgU/gtT+4d+2Cf62celcnAIe+8WDPGNMdaFy56uCOP7X9XTAUT5qiOkg9vuro4UTqpQovDpsEOvqzPBDXf6mJWm6wfvE3dNyL5YttouRKh/etagw3Crh+7UuN6jfLNlWpXkWClU6uSznx9RFHr+bZONNS9s40zAHlJnv4qEWm2MbyhQhOYuLHUe+c9YGnFNmYw/lZIBr6BXOmY7TwQFVTAtRYHGbPfpKkwkfLnfcaRx3f/156Ar6ufXPuNQVvGBC2sWy62/MROAgPEz+gm5p461gJrMhXHM7VHAmsiU4DeyU7BwxYFVCKLeI+KbaU0nfeFe4oqbV9JSlu/YQNMAcvYiVie3hQfVaMYiG5/BrUVawZ+UBWt3QVqxLYr6C9wKoz36ycUQKQsWcDLepf9swKptRHLXmf7xvaPm7mlfjU1l4qvTS+v+Ar7CCYeLEbWIN8y0RXeQ9RqwFh6VK3NUx9dWHpfz2hMf25zgcrtztjuIVJIvSp1jUqhQm0dDPY0MVYvTxBzR3Y+EfvO9kqcC6EWTfsfN2fS6iVuqladuPerV/uVkd+3NLaXextlAQeWdw3iKReQIgv8GRxIm3aLMNAdiRGC/X/10E9SR6iFd+tB2uu4usZpxWvVUlllBPsm+0eKIqHb1bTP/cOLNF3V2IQUw7LIZUDiZEGZhZwYEd1cxIVSFABF6TLFn10Xn/7+vazwp4gCNlqhzEOjgxM2QhUqNiAp+G/e1tYdWUep',
            'RadioButtonList2': '空调',
            'RadioButtonList1': '西校区',
            'DropDownList1': '3156',
            'DropDownList2': '5',
            'DropDownList3': '18866',
            'btn_submit': '查询'
        }

    return obj


# 获取电量
def obtain_power(power_type: Power_Type) -> float:
    # 构造请求
    url = "https://hqfw.sdut.edu.cn/stu_elc.aspx"
    headers = {
        "Host": "hqfw.sdut.edu.cn",
        "Connection": "keep-alive",
        "Content-Length": "5013",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://hqfw.sdut.edu.cn",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.27",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://hqfw.sdut.edu.cn/stu_elc.aspx",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": "ASP.NET_SessionId=; gonghao=; name=; bianzhi="
    }
    data = get_webforms_data(power_type)

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


# 获取请求时间
def get_request_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 规则
async def group_checker(event: GroupMessageEvent) -> bool:
    return event.group_id == 982215318 or event.group_id == 442115556


async def tome_checker() -> bool:
    return to_me()


rules = Rule(group_checker, tome_checker)


# 响应器
get_all_power = on_command("宿舍电量", rule=rules, aliases={
    '电量', '电费', "宿舍电费"}, priority=98, block=True)

get_socket_power = on_command("照明电量", rule=rules, aliases={
    '照明', '插座', "照明电费", "插座电费"}, priority=99, block=True)

get_ac_power = on_command("空调电量", rule=rules, aliases={
    '空调', "空调电费"}, priority=99, block=True)


@get_all_power.handle()
async def all_power_check():
    socket_power = obtain_power(Power_Type.SOCKET)
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    str = f"#{check_time}\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)\n剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
    if (socket_power < 10) and (ac_power < 10):
        str = str + "照明和空调都要没电了喵，赶紧交电费喵"
    elif (socket_power < 10):
        str = str + "照明要没电了喵，赶紧交电费喵"
    elif (ac_power < 10):
        str = str + "空调要没电了喵，赶紧交电费喵"
    else:
        str = str + "电量还很充足喵"

    await get_all_power.finish(str)


@get_socket_power.handle()
async def socket_power_check():
    check_time = get_request_time()
    socket_power = obtain_power(Power_Type.SOCKET)

    str = f"#{check_time}\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)\n"
    if (socket_power < 10):
        str = str + "照明要没电了喵，赶紧交电费喵"
    else:
        str = str + "电量还很充足喵"

    await get_socket_power.finish(str)


@get_ac_power.handle()
async def kt_battery_check():
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    str = f"#{check_time}\n剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
    if (ac_power < 10):
        str = str + "空调要没电了喵，赶紧交电费喵"
    else:
        str = str + "电量还很充足喵"

    await get_ac_power.finish(str)


# 定时器
is_noticed: bool = False


async def auto_check_power():
    # 睡眠规避
    current_hour = datetime.datetime.now().hour
    if current_hour < 10 or current_hour >= 24:
        return

    # 获取当前电量
    socket_power = obtain_power(Power_Type.SOCKET)
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    # 低电量提醒
    global is_noticed
    if socket_power < 10 or ac_power < 10:
        # 重复规避
        if is_noticed:
            return

        # 文本处理
        str = f"#{check_time}\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)\n剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
        if (socket_power < 10) and (ac_power < 10):
            str = str + "照明和空调都要没电了喵，赶紧交电费喵"
        elif (socket_power < 10):
            str = str + "照明要没电了喵，赶紧交电费喵"
        elif (ac_power < 10):
            str = str + "空调要没电了喵，赶紧交电费喵"
        else:
            str = str + "电量还很充足喵"

        # 发送提醒
        bot, = get_bots().values()
        await bot.send_group_msg(
            group_id=982215318,
            message=str
        )
        is_noticed = True

    elif is_noticed:
        is_noticed = False

scheduler.add_job(auto_check_power, "interval",
                  hours=2, id="auto_check_power")
