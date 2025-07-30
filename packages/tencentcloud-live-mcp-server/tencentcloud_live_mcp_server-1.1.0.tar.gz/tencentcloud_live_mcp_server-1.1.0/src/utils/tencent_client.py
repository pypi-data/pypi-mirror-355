#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@File    : tencent_client.py
@Time    : 2025/05/30
@Author  : willsygao
@Desc    : 腾讯云API客户端基类
"""

from typing import Any, Dict, Optional

from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

from utils.config import config
from utils.logger import setup_logger

logger = setup_logger("tencent_client")


class TencentCloudClient:
    """腾讯云API客户端基类"""

    def __init__(
            self,
            service: str,
            version: str,
            endpoint: str,
            region: Optional[str] = None
    ):
        """
        初始化腾讯云API客户端

        Args:
            service: 服务名称
            version: API版本
            endpoint: API端点
            region: 区域，默认使用配置中的区域
        """
        self.service = service
        self.version = version
        self.endpoint = endpoint
        self.region = region or ""
        self.client = self._create_client()

    def _create_client(self) -> CommonClient:
        """创建腾讯云API客户端"""
        try:
            # 创建凭证
            cred = credential.Credential(config.SECRET_ID, config.SECRET_KEY)

            # 创建HTTP配置
            http_profile = HttpProfile()
            http_profile.endpoint = self.endpoint

            # 创建客户端配置
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile

            # 创建客户端
            return CommonClient(
                self.service,
                self.version,
                cred,
                self.region,
                profile=client_profile
            )
        except Exception as e:
            logger.error(f"创建腾讯云API客户端失败: {e}")
            raise

    def call_api(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用腾讯云API

        Args:
            action: API操作名称
            params: API参数，默认为空字典

        Returns:
            API响应结果

        Raises:
            TencentCloudSDKException: API调用失败
        """
        if params is None:
            params = {}

        try:
            logger.info(f"调用API: {action}, 参数: {params}")
            response = self.client.call_json(action, params)
            return response
        except TencentCloudSDKException as e:
            logger.error(f"API调用失败: {e}")
            raise
