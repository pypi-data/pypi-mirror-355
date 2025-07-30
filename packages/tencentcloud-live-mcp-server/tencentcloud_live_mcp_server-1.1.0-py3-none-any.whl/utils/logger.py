#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@File    : logger.py
@Time    : 2025/05/30
@Author  : willsygao
@Desc    : 日志记录模块
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    设置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别，默认为DEBUG

    Returns:
        配置好的日志记录器
    """
    if level is None:
        level = logging.DEBUG

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
