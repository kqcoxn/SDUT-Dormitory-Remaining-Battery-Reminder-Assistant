from nonebot import get_driver, on_command, require, get_bots
from nonebot.rule import to_me
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.params import CommandArg
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
    is_reported = False
    if len(power_list) > 2:
        is_reported = True
    history_data[get_now_date()] = [(socket_power if socket_power else power_list[0]),
                                    (ac_power if ac_power else power_list[1]), (power_list[2] if is_reported else 0), (power_list[3] if is_reported else 0)]

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
    '电量', '电费', "宿舍电费"}, priority=99, block=True)

get_today_delta = on_command("今日耗电", rule=rules, aliases={
    '今日用电', "今日电量"}, priority=100, block=True)

get_yesterday_delta = on_command("昨日耗电", rule=rules, aliases={
    '昨日用电', "昨日电量"}, priority=100, block=True)

report_charging = on_command("充电记录", rule=rules, aliases={
    '上报充电', "充电"}, priority=101, block=True)


@get_all_power.handle()
async def all_power_check():
    # 获取电量
    socket_power = obtain_power(Power_Type.SOCKET)
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

    # 记录电量
    record_history(socket_power, ac_power)

    # 合成文本
    str = f"#{check_time}\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)\n"
    if settings["is_open_AC"]:
        str = str + f"剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
    if (socket_power < settings["warning_value"]) and (ac_power < settings["warning_value"]) and settings["is_open_AC"]:
        str = str + "照明和空调都要没电了喵，赶紧交电费喵"
    elif (socket_power < settings["warning_value"]):
        str = str + "照明要没电了喵，赶紧交电费喵"
    elif (ac_power < settings["warning_value"]) and settings["is_open_AC"]:
        str = str + "空调要没电了喵，赶紧交电费喵"
    else:
        str = str + "电量还很充足喵"

    await get_all_power.finish(str)


@get_today_delta.handle()
async def today_delta_check():
    # 保存当前电量
    record_history(obtain_power(Power_Type.SOCKET),
                   obtain_power(Power_Type.AC))

    # 计算耗电量
    try:
        today_power = history_data[get_now_date()]
        yesterday_power = history_data[get_last_Ndate_date(1)]
        socket_delta = yesterday_power[0] - today_power[0] + today_power[2]
        ac_delta = yesterday_power[1] - today_power[1] + today_power[3]

        # 合成文本
        str = f"今日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)"
        if settings["is_open_AC"]:
            str = str + \
                f"\n今日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)"
        await get_today_delta.finish(str)
    except Exception:
        pass


@get_yesterday_delta.handle()
async def yesterday_delta_check():
    # 计算耗电量
    try:
        last_1days_power = history_data[get_last_Ndate_date(1)]
        last_2days_power = history_data[get_last_Ndate_date(2)]
        socket_delta = last_2days_power[0] - \
            last_1days_power[0] + last_1days_power[2]
        ac_delta = last_2days_power[1] - \
            last_1days_power[1] + last_1days_power[3]

        # 合成文本
        str = f"今日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)"
        if settings["is_open_AC"]:
            str = str + \
                f"\n今日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)"
        await get_today_delta.finish(str)
    except Exception:
        pass


@report_charging.handle()
async def handle_function(args: Message = CommandArg()):
    if message := args.extract_plain_text():
        # 读取指令
        msgs = message.split()
        if len(msgs) < 2:
            await report_charging.finish("参数错误，格式为“充电 [充电种类(照明/空调)] [充电金额]”")
        type = msgs[0]
        amount = float(msgs[1])

        # 设置充电量
        history_data[get_now_date()][3 if (
            type == "空调") else 2] = amount

        # 保存数据
        record_history(obtain_power(Power_Type.SOCKET),
                       obtain_power(Power_Type.AC))

        await report_charging.finish(f"已记录{type}充电 {amount} ￥({round(amount/0.55,2)} kW·h)")
    else:
        await report_charging.finish("请输入充电种类与充电金额喵")


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
    if socket_power < settings["warning_value"] or (settings["is_open_AC"] and ac_power < settings["warning_value"]):
        # 重复规避
        if is_noticed:
            return

        # 合成文本
        str = f"#{check_time}\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)\n"
        if settings["is_open_AC"]:
            str = str + \
                f"剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
        if (socket_power < settings["warning_value"]) and (ac_power < settings["warning_value"]) and settings["is_open_AC"]:
            str = str + "照明和空调都要没电了喵，赶紧交电费喵"
        elif (socket_power < settings["warning_value"]):
            str = str + "照明要没电了喵，赶紧交电费喵"
        elif (ac_power < settings["warning_value"]) and settings["is_open_AC"]:
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
    # 记录
    socket_power = obtain_power(Power_Type.SOCKET)
    ac_power = obtain_power(Power_Type.AC)
    record_history(socket_power, ac_power)

    # 汇报
    if settings["is_daily_report"]:
        target_group = settings["target_group"]
        if target_group:
            bot, = get_bots().values()
            # 计算耗电量
            today_power = history_data[get_now_date()]
            yesterday_power = history_data[get_last_Ndate_date(1)]
            socket_delta = yesterday_power[0] - today_power[0] + today_power[2]
            ac_delta = yesterday_power[1] - today_power[1] + today_power[3]

            # 发送消息
            str = f"#{get_now_date()}\n今日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)"
            if settings["is_open_AC"]:
                str = str + \
                    f"\n今日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)"
            str = str + \
                f"\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)"
            if settings["is_open_AC"]:
                str = str + \
                    f"剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)\n"
            str = str + "\n晚安喵~"
            await bot.send_group_msg(
                group_id=target_group,
                message=str
            )

scheduler.add_job(auto_check_power, "cron", hour='23',
                  minute='58', id="daily_check_power")
