#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
@author: feng jiaxin
@file: setup.py
@time 2025/07/03 16:12
@desc
"""
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    'packages': ['server','config','fastapi','uvicorn'],   # 依赖的包，python自己无法找到的包
    'excludes': []  # 不包含那些包
}

setup(
    name='csmServer',
    version='1.0',
    description='csm服务，提取信息、等级测评等关键信息',
    options={'build_exe': build_exe_options},
    executables=[
        Executable(
            'startup.py',  # 入口文件
            target_name='csmServer'  # 打包程序名
        )
    ]
)