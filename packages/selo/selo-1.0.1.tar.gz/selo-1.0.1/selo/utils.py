import json
import os
from datetime import datetime

import yaml
import pyautogui

def assert_equal(actual, expected, msg=''):
    assert actual == expected, f"{msg} => 预期: {expected}, 实际: {actual}"

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def timestamp():
    return int(datetime.now().timestamp())

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data

def take_screenshot(save_dir='screenshots'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    times = now_str()
    filepath = os.path.join(save_dir, f'screenshot_{times}.png')
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    print(f"Screenshot saved to {filepath}")
    return filepath