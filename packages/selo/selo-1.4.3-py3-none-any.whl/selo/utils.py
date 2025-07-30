import json
import os
from datetime import datetime

import yaml
import pyautogui

def assert_equal(actual, expected, msg=''):
    """
    断言
    :param actual: 实际
    :param expected: 预期
    :param msg:
    :return:
    """
    assert actual == expected, f"{msg} => 预期: {expected}, 实际: {actual}"

def now_str():
    """
    获取当前时间:年-月-日-时-分-秒格式
    :return:
    """
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

def timestamp():
    """
    获取当前时间戳
    :return:
    """
    return int(datetime.now().timestamp())

def read_json(path):
    """
    读取json
    :param path: 文件路径
    :return:
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path, data):
    """
    写入json
    :param path: 文件路径
    :param data: 数据
    :return:
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_yaml(file_path):
    """
    读取yaml
    :param file_path: 文件路径
    :return:
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data

def take_screenshot(save_dir='screenshots'):
    """
    截图
    :param save_dir: 保存目录
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    times = now_str()
    filepath = os.path.join(save_dir, f'screenshot_{times}.png')
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)