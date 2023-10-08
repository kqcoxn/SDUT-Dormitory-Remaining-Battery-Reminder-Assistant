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
from datetime import datetime, timedelta
import json
import os


# json读取
def get_data(file_name: str) -> dict:
    # 获取文件路径
    current_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(
        current_directory, 'data', file_name + '.json')

    # 读取JSON文件
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            return data
    except Exception:
        return {"error": "配置文件不存在！"}


# 加载配置
global_config = get_driver().config
config = Config.parse_obj(global_config)
settings: dict = get_data("Config")
history_data: dict = get_data("History")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 引入依赖
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


# 查询类型枚举
class Power_Type(Enum):
    SOCKET = 1
    AC = 2


# 错误值枚举
class Error_Type(Enum):
    NETWORK_ERROR = -1
    PARAM_ERROR = -2
    OTHER_ERROR = -999


# 获取请求模板
def get_request_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 获取日期
def get_now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# 获取前n天日期
def get_last_Ndate_date(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


# 写入记录
def record_history(socket_power: float, ac_power: float):
    # 整理数值
    power_list = []
    try:
        power_list = history_data[get_now_date()]
    except Exception:
        pass
    history_data[get_now_date()] = [(socket_power if socket_power else power_list[0]),
                                    (ac_power if ac_power else power_list[1])]

    # 写入
    current_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(
        current_directory, 'data', 'History.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(history_data, json_file)


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


# 初始化电量
record_history(obtain_power(Power_Type.SOCKET), obtain_power(Power_Type.AC))


# 规则
async def group_checker(group_event: GroupMessageEvent) -> bool:
    return settings["groups"].count(group_event.group_id) > 0


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

get_today_delta = on_command("今日耗电", rule=rules, aliases={
    '今日用电', "今日电量"}, priority=99, block=True)

get_yesterday_delta = on_command("昨日耗电", rule=rules, aliases={
    '昨日用电', "昨日电量"}, priority=99, block=True)


@get_all_power.handle()
async def all_power_check():
    # 获取电量
    socket_power = obtain_power(Power_Type.SOCKET)
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    # 记录电量
    record_history(socket_power, ac_power)

    # 合成文本
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
    # 获取电量
    check_time = get_request_time()
    socket_power = obtain_power(Power_Type.SOCKET)

    # 记录电量
    record_history(socket_power)

    # 合成文本
    str = f"#{check_time}\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)\n"
    if (socket_power < 10):
        str = str + "照明要没电了喵，赶紧交电费喵"
    else:
        str = str + "电量还很充足喵"

    await get_socket_power.finish(str)


@get_ac_power.handle()
async def kt_power_check():
    # 获取电量
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    # 记录电量
    record_history(ac_power=ac_power)

    # 合成文本
    str = f"#{check_time}\n剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
    if (ac_power < 10):
        str = str + "空调要没电了喵，赶紧交电费喵"
    else:
        str = str + "电量还很充足喵"

    await get_ac_power.finish(str)


@get_today_delta.handle()
async def today_delta_check():
    # 保存当前电量
    record_history(obtain_power(Power_Type.SOCKET),
                   obtain_power(Power_Type.AC))

    # 计算耗电量
    try:
        today_power = history_data[get_now_date()]
        yesterday_power = history_data[get_last_Ndate_date(1)]
        socket_delta = yesterday_power[0] - today_power[0]
        ac_delta = yesterday_power[1] - today_power[1]

        if socket_delta < 0 or ac_delta < 0:
            await get_ac_power.finish("未上报充电量，无法计算耗电量！")

        await get_ac_power.finish(f"今日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)\n今日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)")
    except Exception:
        pass


@get_yesterday_delta.handle()
async def yesterday_delta_check():
    # 计算耗电量
    try:
        last_1days_power = history_data[get_last_Ndate_date(1)]
        last_2days_power = history_data[get_last_Ndate_date(2)]
        socket_delta = last_2days_power[0] - last_1days_power[0]
        ac_delta = last_2days_power[1] - last_1days_power[1]

        if socket_delta > 0 or ac_delta > 0:
            await get_ac_power.finish("未上报当日充电量，无法计算耗电量！")

        await get_ac_power.finish(f"昨日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)\n昨日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)")
    except Exception:
        pass


# 定时查询
is_noticed: bool = False


async def auto_check_power():
    # 睡眠规避
    current_hour = datetime.now().hour
    if current_hour < 10 or current_hour >= 24:
        return

    # 获取当前电量
    socket_power = obtain_power(Power_Type.SOCKET)
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    # 记录电量
    record_history(socket_power, ac_power)

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
        target_group = settings["target_group"]
        if target_group:
            bot, = get_bots().values()
            await bot.send_group_msg(
                group_id=target_group,
                message=str
            )
        is_noticed = True

    elif is_noticed:
        is_noticed = False

scheduler.add_job(auto_check_power, "interval",
                  hours=2, id="auto_check_power")


# 记录当日电量
async def daily_check_power():
    record_history(obtain_power(Power_Type.SOCKET),
                   obtain_power(Power_Type.AC))

scheduler.add_job(auto_check_power, "cron", hour='23',
                  minute='58', id="daily_check_power")
