"""
Netease Minecraft Nickname Random by wangyupu
使用来自网易的词典
全部使用built-in库
可自定义
"""

import hashlib
import json
import os
import random
import time
from pathlib import Path

from nonebot_plugin_localstore import get_plugin_config_dir

application_start_time = time.time()
config_dir = get_plugin_config_dir()
# 获取目录
path = __file__
path = path[: len(path) - 7]
cwd = Path(path)

# 处理db
dbfs = os.listdir(cwd / "db")
dbs = {}
f2s = {}
try:
    dbfs.remove(".DS_Store")
    dbfs.remove("字到音")
except:  # noqa: E722
    pass

# 写入变量
for filename in dbfs:
    with open(f"{path}db/{filename}") as file:
        dbs[filename] = file.read().split("\n")

with open(f"{path}db/字到音") as file:
    lines = file.read().split("\n")
    for item in lines:
        lineitems = item.split(",")
        f2s[lineitems[0]] = lineitems[1]
if not (config_dir/"name_strus.json").is_file() or not (config_dir/"name_strus.json").exists():
    with open(f"{path}name_strus.json") as file:
        name_stru: dict[str, str] = json.load(file)
    with open(config_dir/"name_strus.json", "w") as f:
        json.dump(name_stru, f,indent=4)
else:
    with open(config_dir/"name_strus.json") as file:
        name_stru: dict[str, str] = json.load(file)

name_stru_keys = list(name_stru.keys())


# 主
def init_random():
    seed = (hashlib.sha512(str(time.time()).encode()).hexdigest())[:8]
    seed = int(seed, 16)
    ##print(f"初始化到种子{seed}")
    random.seed(seed)


def get_random_nickname():
    nickname_type = random.choice(name_stru_keys)
    nick = ""
    parts = []

    thisnickname_stru = (name_stru[nickname_type]).split("+")
    for item in thisnickname_stru:
        if str(item)[0] == "#":
            thispart = item[1:]
        else:
            thispart = random.choice(dbs[item])
        parts.append(thispart)
        nick = nick + thispart

    return nick
