#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@File    : config.py
@Time    : 2025/05/30
@Author  : willsygao
@Desc    : 腾讯云API服务器配置文件
"""


import os


class Config:
    """配置管理类"""

    # 腾讯云API凭证
    SECRET_ID = os.getenv("TENCENTCLOUD_SECRET_ID", "")
    SECRET_KEY = os.getenv("TENCENTCLOUD_SECRET_KEY", "")

    # 区域配置
    DEFAULT_REGION = os.getenv("DEFAULT_REGION", "ap-guangzhou")

    # API版本配置
    LIVE_API_VERSION = "2018-08-01"

    # API端点
    LIVE_ENDPOINT = "live.tencentcloudapi.com"


config = Config()
