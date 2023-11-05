from nonebot import get_driver, on_command, require, get_bots
from nonebot.rule import to_me
from nonebot.rule import Rule
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.params import CommandArg
from .config import Config
from enum import Enum
import warnings
import requests
from requests import RequestsDependencyWarning
from datetime import datetime, timedelta
import json
import os


# 禁用警告
warnings.simplefilter("ignore", category=RequestsDependencyWarning)


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

# 引入依赖
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


# 查询类型枚举
class Power_Type(Enum):
    SOCKET = 1
    AC = 2


# 获取完整日期
def get_request_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 获取日期
def get_now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# 获取前n天日期
def get_last_Ndate_date(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


# 保存配置
def record_settings():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(
        current_directory, 'data', 'Config.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(settings, json_file)


# 获取电量
def obtain_power(power_type: Power_Type, gap: int = -1) -> float:
    # 构造请求
    if gap == -1:
        url = settings["api"]["socket"] if power_type == Power_Type.SOCKET else settings["api"]["ac"]
    elif gap == 0:
        url = settings["api"]["l1"]["socket"] if power_type == Power_Type.SOCKET else settings["api"]["l1"]["ac"]
    else:
        url = settings["api"]["l2"]["socket"] if power_type == Power_Type.SOCKET else settings["api"]["l2"]["ac"]
    url = url.replace("|port|", str(settings["port"]))

    # 请求数据
    try:
        response = requests.get(url, verify=False)
        return float(response.text)
    except Exception:
        return -1


# 上传数据
def update_cost(addedSocketCost=0, addedACCost=0) -> int:
    # 构造请求
    url = settings["update"]["powerHistory"] + f"?addedSocketCost={addedSocketCost}&addedACCost={addedACCost}"
    url = url.replace("|port|", str(settings["port"]))

    # 请求数据
    try:
        response = requests.post(url, verify=False)
        if response.text == "{'status'='done'}":
            return 0
    except Exception:
        return -1


# 规则
async def group_checker(group_event: GroupMessageEvent) -> bool:
    return settings["groups"].count(group_event.group_id) > 0


async def tome_checker() -> bool:
    return to_me()


rules = Rule(group_checker, tome_checker)


# 宿舍电量响应
get_all_power = on_command("宿舍电量", rule=rules, aliases={
    '电量', '电费', "宿舍电费"}, priority=99, block=True)


@get_all_power.handle()
async def all_power_check():
    # 获取电量
    socket_power = obtain_power(Power_Type.SOCKET)
    ac_power = obtain_power(Power_Type.AC)

    # 合成文本
    check_time = get_request_time()
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


# 今日用电响应
get_today_delta = on_command("今日耗电", rule=rules, aliases={
    '今日用电', "今日电量"}, priority=100, block=True)


@get_today_delta.handle()
async def today_delta_check():
    # 计算耗电量
    try:
        socket_delta = obtain_power(Power_Type.SOCKET, 0)
        if settings["is_open_AC"]:
            ac_delta = obtain_power(Power_Type.AC, 0)

        # 合成文本
        str = f"今日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)"
        if settings["is_open_AC"]:
            str = str + \
                f"\n今日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)"
        await get_today_delta.finish(str)
    except Exception:
        pass


# 昨日用电响应
get_yesterday_delta = on_command("昨日耗电", rule=rules, aliases={
    '昨日用电', "昨日电量"}, priority=100, block=True)


@get_yesterday_delta.handle()
async def yesterday_delta_check():
    # 计算耗电量
    try:
        socket_delta = obtain_power(Power_Type.SOCKET, 1)
        if settings["is_open_AC"]:
            ac_delta = obtain_power(Power_Type.AC, 1)

        # 合成文本
        str = f"昨日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)"
        if settings["is_open_AC"]:
            str = str + \
                f"\n昨日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)"
        await get_today_delta.finish(str)
    except Exception:
        pass


# 上报充电响应
report_charging = on_command("充电记录", rule=rules, aliases={
    '上报充电', "充电"}, priority=101, block=True)


@report_charging.handle()
async def handle_function(args: Message = CommandArg()):
    if message := args.extract_plain_text():
        # 读取指令
        msgs = message.split()
        if len(msgs) < 2:
            await report_charging.finish("参数错误，格式为“充电 [充电种类(照明/空调)] [充电金额]”")
        type = msgs[0]
        amount = float(msgs[1])

        # 上传数据
        update_cost(amount if type == "照明" else 0, amount if type == "空调" else 0)

        await report_charging.finish(f"已记录{type}充电 {amount}￥({round(amount/0.55,2)} kW·h)")
    else:
        await report_charging.finish("请输入充电种类与充电金额喵")


# 热重载响应
overload_settings = on_command("热重载电量配置", aliases={
    '热重载电量设置'}, rule=rules, priority=101, block=True)


@overload_settings.handle()
async def overload_setting():
    global settings
    settings = get_data("Config")
    await overload_settings.finish("配置热重载成功！")


# 开关空调用电响应
set_AC = on_command("空调检测", rule=rules, priority=101, block=True)


@set_AC.handle()
async def set_ac(args: Message = CommandArg()):
    if message := args.extract_plain_text():
        # 更改配置
        settings["is_open_AC"] = True if (
            message == "开" or message == "打开") else False

        # 保存配置
        record_settings()

        await set_AC.finish(f"已{'打开' if settings['is_open_AC'] else '关闭'}空调检测")
    else:
        await set_AC.finish("请输入开/关指令")


# 定时查询
is_noticed: bool = False


async def auto_check_power():
    # 睡眠规避
    current_hour = datetime.now().hour
    if current_hour < 8 or current_hour >= 24:
        return

    # 获取当前电量
    socket_power = obtain_power(Power_Type.SOCKET)
    check_time = get_request_time()
    ac_power = obtain_power(Power_Type.AC)

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
                  hours=settings["auto_interval"], id="auto_check_power")


# 记录当日电量
async def daily_check_power():
    # 汇报
    if settings["is_daily_report"]:
        target_group = settings["target_group"]
        if target_group:
            bot, = get_bots().values()
            # 请求电量
            socket_power = obtain_power(Power_Type.SOCKET)
            ac_power = obtain_power(Power_Type.AC)
            socket_delta = obtain_power(Power_Type.SOCKET, 0)
            ac_delta = obtain_power(Power_Type.AC, 0)

            # 发送消息
            str = f"#{get_now_date()}#\n剩余照明电量: {socket_power} kW·h ({round(socket_power*0.55, 2)}￥)"
            if settings["is_open_AC"]:
                str = str + \
                    f"\n剩余空调电量: {ac_power} kW·h ({round(ac_power*0.55, 2)}￥)"
            str = str + \
                f"\n—————\n今日照明耗电: {round(socket_delta, 2)} kW·h ({round(socket_delta*0.55, 2)}￥)"
            if settings["is_open_AC"]:
                str = str + \
                    f"\n今日空调耗电: {round(ac_delta, 2)} kW·h ({round(ac_delta*0.55, 2)}￥)"
            str = str + "\n\n晚安喵，记得关灯~"
            await bot.send_group_msg(
                group_id=target_group,
                message=str
            )

scheduler.add_job(daily_check_power, "cron", hour=settings["record_time"][0],
                  minute=settings["record_time"][1], id="daily_check_power")
