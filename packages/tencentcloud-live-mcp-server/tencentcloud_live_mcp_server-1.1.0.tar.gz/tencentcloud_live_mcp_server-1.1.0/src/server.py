#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@File    : server.py
@Time    : 2025/05/30
@Author  : willsygao
@Version : 1.0
@Desc    : 基于MCP的腾讯云API服务器主文件
"""

# 标准库导入
import json
import random
import sys
import time
import hmac
import base64
import hashlib
import requests
import argparse
from datetime import datetime, timedelta
import time

# 第三方库导入
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

# 类型提示导入
from typing import Dict, Any, List, Optional, Union

# 本地模块导入
from tools.live_api import LiveClient
from utils.logger import setup_logger
from utils.config import config

MCP_SERVER_NAME = "tencent-cloud-mcp-server"

# 设置日志
logger = setup_logger(MCP_SERVER_NAME)

# MD5
def md5_encrypt(input_string):
    # 创建一个MD5哈希对象
    md5_hash = hashlib.md5()

    # 将输入字符串编码为字节
    input_bytes = input_string.encode('utf-8')

    # 更新哈希值
    md5_hash.update(input_bytes)

    # 获取十六进制格式的哈希值
    return md5_hash.hexdigest()

# 创建MCP服务器实例
mcp = FastMCP(
    MCP_SERVER_NAME,
    instructions="""
    # 腾讯云API服务
    
    本服务基于Model Context Protocol（MCP）实现提供腾讯云直播API调用Tools的MCP Server
    
    提供腾讯云直播域名管理、拉流转推、直播流管理和流管理等相关接口

    """,
    dependencies=[
        "tencentcloud-sdk-python",
        "pydantic",
        "loguru"
    ]
)


# <---------------------获取推流地址---------------------> #
@mcp.tool()
async def describe_rtmp_addr(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        ),
        app_name: str = Field(
            default=None,
            description="区分同一个域名下多个 App 的地址路径，默认为 live"
        ),
        stream_name: str = Field(
            default=None,
            description="自定义的流名称，每路直播流的唯一标识符"
        ),
        expire_time: Optional[int] = Field(
            default=7,
            description="过期时间。默认：7天"
        )
) -> str:
    """
    获取推流地址

        Args:
            domain_name: 推流域名
            app_name: 区分同一个域名下多个 App 的地址路径
            stream_name: 流名称
            expire_time: 过期时间(optional)

        Returns:
            PushAuthKeyInfo: 推流鉴权key信息
            RTMPAddr: RTMP地址
            请求ID
    """
    logger.info(f"获取推流地址: domain_name={domain_name}, app_name={app_name},"
                f"stream_name={stream_name}, expire_time={expire_time}")

    try:
        live_client = LiveClient()
        # 获取鉴权key
        result = live_client.describe_live_push_auth_key(
            domain_name=domain_name
        )
        logger.info(f"获取鉴权key: result={result}")
        # 主鉴权key
        push_auth_key_info = result['Response']['PushAuthKeyInfo']
        master_auth_key = push_auth_key_info['MasterAuthKey']
        logger.info(f"push_auth_key_info={push_auth_key_info}, master_auth_key={master_auth_key}")
        # UNIX时间戳
        expire_delay = timedelta(days=expire_time)
        future_time = datetime.now() + expire_delay
        unix_timestamp = future_time.timestamp()
        hex_timestamp = format(int(hex(int(unix_timestamp)), 16), 'X')
        logger.info(f"过期时间的UNIX16进制时间戳：hex_timestamp={hex_timestamp}")
        # MD5拼接
        str_for_md5 = master_auth_key + stream_name + hex_timestamp
        md5_str = md5_encrypt(str_for_md5)
        logger.info(f"MD5拼接：{str_for_md5},txSecret={md5_str}")
        # rtmp地址拼接
        str_for_rtmp = ('rtmp://' + domain_name + '/' + app_name + '/'
                        + stream_name + '?' + 'txSecret=' + md5_str + '&' + 'txTime=' + hex_timestamp)
        logger.info(f"rtmp地址={str_for_rtmp}")
        result['Response']['RTMPAddr'] = str_for_rtmp
        # 返回result
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"获取推流地址失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# <---------------------获取播放地址---------------------> #
@mcp.tool()
async def describe_play_addr(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        ),
        app_name: str = Field(
            default=None,
            description="区分同一个域名下多个 App 的地址路径，默认为 live"
        ),
        stream_name: str = Field(
            default=None,
            description="自定义的流名称，每路直播流的唯一标识符"
        ),
        expire_time: Optional[int] = Field(
            default=7,
            description="过期时间。默认：7天"
        ),
        transcode_template: Optional[int] = Field(
            default=None,
            description="转码模版ID"
        )
) -> str:
    """
    获取播放地址

        Args:
            domain_name: 推流域名
            app_name: 区分同一个域名下多个 App 的地址路径
            stream_name: 流名称
            expire_time: 过期时间(optional)
            transcode_template: 转码模版ID(optional)

        Returns:
            PushAuthKeyInfo: 推流鉴权key信息
            RTMPAddr: RTMP地址
            请求ID
    """
    logger.info(f"获取播放地址: domain_name={domain_name}, app_name={app_name},"
                f"stream_name={stream_name}, expire_time={expire_time}")

    try:
        live_client = LiveClient()
        # 获取鉴权key
        result = live_client.describe_live_play_auth_key(
            domain_name=domain_name
        )
        logger.info(f"获取鉴权key: result={result}")

        # rtmp地址拼接
        basic_addr = '://' + domain_name + '/' + app_name + '/' + stream_name
        # str_for_rtmp = ('rtmp://' + domain_name + '/' + app_name + '/' + stream_name)
        # str_for_flv = ('http://' + domain_name + '/' + app_name + '/' + stream_name)
        # str_for_hls = ('http://' + domain_name + '/' + app_name + '/' + stream_name)
        if transcode_template is not None:
            basic_addr += '_' + str(transcode_template)
        if result['Response']['PlayAuthKeyInfo']['Enable'] is 1:
            # 主鉴权key
            play_auth_key_info = result['Response']['PlayAuthKeyInfo']
            master_auth_key = play_auth_key_info['AuthKey']
            logger.info(f"play_auth_key_info={play_auth_key_info}, master_auth_key={master_auth_key}")
            # UNIX时间戳
            expire_delay = timedelta(days=expire_time)
            future_time = datetime.now() + expire_delay
            unix_timestamp = future_time.timestamp()
            hex_timestamp = format(int(hex(int(unix_timestamp)), 16), 'X')
            logger.info(f"过期时间的UNIX16进制时间戳：hex_timestamp={hex_timestamp}")
            # MD5拼接
            str_for_md5 = master_auth_key + stream_name + hex_timestamp
            md5_str = md5_encrypt(str_for_md5)
            logger.info(f"MD5拼接：{str_for_md5}, txSecret={md5_str}")
            basic_addr += '?' + 'txSecret=' + md5_str + '&' + 'txTime=' + hex_timestamp

        str_for_rtmp = 'rtmp' + basic_addr
        str_for_flv = 'http' + basic_addr + '.flv'
        str_for_hls = 'http' + basic_addr + '.m3u8'

        logger.info(f"rtmp地址={str_for_rtmp}, flv地址={str_for_flv}, hls地址={str_for_hls}")
        result['Response']['RTMPAddr'] = str_for_rtmp
        result['Response']['FLVAddr'] = str_for_flv
        result['Response']['HLSAddr'] = str_for_hls
        # 返回result
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"获取播放地址失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# <---------------------域名管理---------------------> #
# 添加域名
@mcp.tool()
async def add_live_domain(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        ),
        domain_type: int = Field(
            default=None,
            description="域名类型，0：推流域名，1：播放域名。示例值：0"
        ),
        play_type: Optional[int] = Field(
            default=None,
            description="拉流域名类型：1：国内，2：全球，3：境外。默认值：1。示例值：1"
        ),
        is_delay_live: Optional[int] = Field(
            default=None,
            description="是否是慢直播：0： 普通直播，1 ：慢直播 。默认值： 0。示例值：1"
        ),
        is_mini_program_live: Optional[int] = Field(
            default=None,
            description="是否是小程序直播：0： 标准直播，1 ：小程序直播 。默认值： 0。示例值：1"
        ),
        verify_owner_type: Optional[str] = Field(
            default=None,
            description="域名归属校验类型"
        )
) -> str:
    """
    添加域名

        Args:
            domain_name: 推流域名
            domain_type: 域名类型
            play_type: 拉流域名类型(optional)
            is_delay_live: 是否是慢直播(optional)
            is_mini_program_live: 是否是小程序直播(optional)
            verify_owner_type: 域名归属校验类型(optional)

        Returns:
            请求ID
    """
    logger.info(f"添加域名: domain_name={domain_name}, domain_type={domain_type}, play_type={play_type}, "
                f"is_delay_live={is_delay_live}, is_mini_program_live={is_mini_program_live}, "
                f"verify_owner_type={verify_owner_type}")

    try:
        live_client = LiveClient()
        result = live_client.add_live_domain(
            domain_name=domain_name,
            domain_type=domain_type,
            play_type=play_type,
            is_delay_live=is_delay_live,
            is_mini_program_live=is_mini_program_live,
            verify_owner_type=verify_owner_type
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"添加域名失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 删除域名
@mcp.tool()
async def delete_live_domain(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        ),
        domain_type: int = Field(
            default=None,
            description="域名类型，0：推流域名，1：播放域名。示例值：0"
        )
) -> str:
    """
    删除域名

        Args:
            domain_name: 推流域名
            domain_type: 域名类型

        Returns:
            请求ID
    """
    logger.info(f"删除域名: domain_name={domain_name}, domain_type={domain_type}")

    try:
        live_client = LiveClient()
        result = live_client.delete_live_domain(
            domain_name=domain_name,
            domain_type=domain_type
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"删除域名失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 启用域名
@mcp.tool()
async def enable_live_domain(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        )
) -> str:
    """
    启用域名

        Args:
            domain_name: 推流域名

        Returns:
            请求ID
    """
    logger.info(f"删除域名: domain_name={domain_name}")

    try:
        live_client = LiveClient()
        result = live_client.enable_live_domain(
            domain_name=domain_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"启用域名失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 禁用域名
@mcp.tool()
async def forbid_live_domain(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        )
) -> str:
    """
    禁用域名

        Args:
            domain_name: 推流域名

        Returns:
            请求ID
    """
    logger.info(f"禁用域名: domain_name={domain_name}")

    try:
        live_client = LiveClient()
        result = live_client.forbid_live_domain(
            domain_name=domain_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"禁用域名失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 查询域名信息
@mcp.tool()
async def describe_live_domain(
        ctx: Context,
        domain_name: str = Field(
            default=None,
            description="域名名称。示例值：www.test.com"
        )
) -> str:
    """
    查询域名信息

        Args:
            domain_name: 推流域名

        Returns:
            DomainInfo: 域名信息
            请求ID
    """
    logger.info(f"查询域名信息: domain_name={domain_name}")

    try:
        live_client = LiveClient()
        result = live_client.describe_live_domain(
            domain_name=domain_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"查询域名信息失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 查询域名列表
@mcp.tool()
async def describe_live_domains(
        ctx: Context,
        domain_status: Optional[int] = Field(
            default=None,
            description="域名状态过滤。0-停用，1-启用。示例值：1"
        ),
        domain_type: Optional[int] = Field(
            default=None,
            description="域名类型，0：推流域名，1：播放域名。示例值：0"
        ),
        page_size: Optional[int] = Field(
            default=None,
            description="分页大小，范围：10~100。默认10。示例值：10"
        ),
        page_num: Optional[int] = Field(
            default=None,
            description="取第几页，范围：1~100000。默认1。示例值：1"
        ),
        is_delay_live: Optional[int] = Field(
            default=None,
            description="0 普通直播 1慢直播 默认0。示例值：0"
        ),
        domain_prefix: Optional[str] = Field(
            default=None,
            description="域名前缀。示例值：qq"
        ),
        play_type: Optional[int] = Field(
            default=None,
            description="播放区域，只在 DomainType=1 时该参数有意义。1: 国内。2: 全球。3: 海外。"
        )
) -> str:
    """
    查询域名列表

        Args:
            domain_status: 域名状态过滤(optional)
            domain_type: 域名类型(optional)
            page_size: 分页大小(optional)
            page_num: 取第几页(optional)
            is_delay_live: 普通直播/慢直播(optional)
            domain_prefix: 域名前缀(optional)
            play_type: 播放区域(optional)

        Returns:
            AllCount: 总记录数
            DomainList: 域名详细信息列表
            CreateLimitCount: 可继续添加域名数量
            PlayTypeCount: 启用的播放域名加速区域统计
            请求ID
    """
    logger.info(f"查询域名列表: domain_status={domain_status}, domain_type={domain_type}, page_size={page_size}, "
                f"page_num={page_num}, is_delay_live={is_delay_live}, "
                f"domain_prefix={domain_prefix}, play_type={play_type}")

    try:
        live_client = LiveClient()
        result = live_client.describe_live_domains(
            domain_status=domain_status,
            domain_type=domain_type,
            page_size=page_size,
            page_num=page_num,
            is_delay_live=is_delay_live,
            domain_prefix=domain_prefix,
            play_type=play_type
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"查询域名列表失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# <---------------------拉流转推---------------------> #
# 删除直播拉流任务
@mcp.tool()
async def delete_live_pull_stream_task(
        ctx: Context,
        region: str = Field(
            default=config.DEFAULT_REGION,
            description="地域"
        ),
        task_id: str = Field(
            default=None,
            description="任务 Id。示例值：9564231"
        ),
        operator: str = Field(
            default=None,
            description="任务 Id。示例值：9564231"
        ),
        specify_task_id: Optional[str] = Field(
            default=None,
            description="指定任务 ID。注意：用于删除使用自定义任务 ID 创建的任务。示例值：myspecifytaskid"
        )
) -> str:
    """
    删除直播拉流任务

        Args:
            region: 地域
            task_id: 任务ID
            operator: 操作人姓名
            specify_task_id: 指定任务ID(optional)

        Returns:
            请求ID
    """
    logger.info(f"删除直播拉流任务: region={region}, task_id={task_id}, "
                f"operator={operator}, specify_task_id={specify_task_id}")

    try:
        live_client = LiveClient(region=region)
        result = live_client.delete_live_pull_stream_task(
            task_id=task_id,
            operator=operator,
            specify_task_id=specify_task_id
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"删除直播拉流任务失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 查询直播拉流任务
@mcp.tool()
async def describe_live_pull_stream_tasks(
        ctx: Context,
        region: str = Field(
            default=config.DEFAULT_REGION,
            description="地域"
        ),
        task_id: str = Field(
            default=None,
            description="任务 Id。来源：调用 CreateLivePullStreamTask 接口时返回。不填默认查询所有任务，按更新时间倒序排序。示例值：9564231"
        ),
        page_num: Optional[int] = Field(
            default=None,
            description="取得第几页，默认值：1。示例值：1"
        ),
        page_size: Optional[int] = Field(
            default=None,
            description="分页大小，默认值：10。取值范围：1~20 之前的任意整数。示例值：10"
        ),
        specify_task_id: Optional[str] = Field(
            default=None,
            description="指定任务 ID。注意：仅供使用指定 ID 创建的任务查询。示例值：myspecifytaskid"
        )
) -> str:
    """
    查询直播拉流任务

        Args:
            region: 地域
            task_id: 任务ID
            page_num: 取得第几页(optional)
            page_size: 分页大小(optional)
            specify_task_id: 指定任务ID(optional)

        Returns:
            TaskInfos: 直播拉流任务信息列表
            PageNum: 分页的页码
            PageSize: 每页大小
            TotalNum: 符合条件的总个数
            TotalPage: 总页数
            LimitTaskNum: 限制可创建的最大任务数
            请求ID
    """
    logger.info(f"查询直播拉流任务: region={region}, task_id={task_id},  page_num={page_num}, "
                f"page_size={page_size}, specify_task_id={specify_task_id}")

    try:
        live_client = LiveClient(region=region)
        result = live_client.describe_live_pull_stream_tasks(
            task_id=task_id,
            page_num=page_num,
            page_size=page_size,
            specify_task_id=specify_task_id
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"查询直播拉流任务失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 创建直播拉流任务
@mcp.tool()
async def create_live_pull_stream_task(
        ctx: Context,
        region: str = Field(
            default=config.DEFAULT_REGION,
            description="地域"
        ),
        source_type: str = Field(
            default=None,
            description="拉流源的类型：PullLivePushLive -直播，PullVodPushLive -点播，PullPicPushLive -图片。示例值：PullLivePushLive"
        ),
        source_urls: List[str] = Field(
            default=None,
            description="拉流源 url 列表，SourceType 为直播（PullLivePushLive）只可以填1个，SourceType 为点播（PullVodPushLive）可以填多个，上限30个。当前支持的文件格式：flv，mp4，hls。当前支持的拉流协议：http，https，rtmp，rtmps，rtsp，srt。"
        ),
        domain_name: str = Field(
            default=None,
            description="推流域名。将拉取过来的流推到该域名"
        ),
        app_name: str = Field(
            default=None,
            description="推流路径。将拉取过来的流推到该路径。"
        ),
        stream_name: str = Field(
            default=None,
            description="推流名称。将拉取过来的流推到该流名称。"
        ),
        start_time: str = Field(
            default=None,
            description="开始时间。使用 UTC 格式时间，例如：2019-01-08T10:00:00Z"
        ),
        end_time: str = Field(
            default=None,
            description="结束时间"
        ),
        operator: str = Field(
            default=None,
            description="任务操作人备注"
        ),
        push_args: Optional[str] = Field(
            default=None,
            description="推流参数。推流时携带自定义参数。"
        ),
        callback_events: Optional[List[str]] = Field(
            default=None,
            description="选择需要回调的事件（不填则回调全部）"
        ),
        vod_loop_times: Optional[str] = Field(
            default=None,
            description="点播拉流转推循环次数，默认：-1"
        ),
        vod_refresh_type: Optional[str] = Field(
            default=None,
            description="点播更新SourceUrls后的播放方式：ImmediateNewSource：立即播放新的拉流源内容；ContinueBreakPoint：播放完当前正在播放的点播 url 后再使用新的拉流源播放。（旧拉流源未播放的点播 url 不会再播放）"
        ),
        callback_url: Optional[str] = Field(
            default=None,
            description="自定义回调地址。拉流转推任务相关事件会回调到该地址。"
        ),
        extra_cmd: Optional[str] = Field(
            default=None,
            description="其他参数"
        ),
        specify_task_id: Optional[str] = Field(
            default=None,
            description="自定义任务 ID"
        ),
        comment: Optional[str] = Field(
            default=None,
            description="任务描述，限制 512 字节"
        ),
        to_url: Optional[str] = Field(
            default=None,
            description="完整目标 URL 地址"
        ),
        file_index: Optional[int] = Field(
            default=None,
            description="指定播放文件索引"
        ),
        offset_time: Optional[int] = Field(
            default=None,
            description="指定播放文件偏移"
        ),
        backup_source_type: Optional[str] = Field(
            default=None,
            description="备源的类型：PullLivePushLive -直播，PullVodPushLive -点播"
        ),
        backup_source_url: Optional[str] = Field(
            default=None,
            description="备源 URL"
        ),
        vod_local_mode: Optional[int] = Field(
            default=None,
            description="点播源是否启用本地推流模式，默认0，不启用"
        ),
        record_template_id: Optional[str] = Field(
            default=None,
            description="录制模板 ID"
        ),
        backup_to_url: Optional[str] = Field(
            default=None,
            description="新的目标地址，用于任务同时推两路场景"
        ),
        transcode_template_name: Optional[str] = Field(
            default=None,
            description="直播转码模板，使用云直播的转码功能进行转码后再转推出去。转码模板需在云直播控制台创建"
        )
) -> str:
    """
    创建直播拉流任务

        Args:
            region: 地域
            source_type: 拉流源的类型
            source_urls: 拉流源 url 列表
            domain_name: 推流域名
            app_name: 推流路径
            stream_name: 推流名称
            start_time: 开始时间
            end_time: 结束时间
            operator: 任务操作人备注
            push_args: 推流参数(optional)
            callback_events: 需要回调的事件(optional)
            vod_loop_times: 点播拉流转推循环次数(optional)
            vod_refresh_type: 点播更新SourceUrls后的播放方式(optional)
            callback_url: 自定义回调地址(optional)
            extra_cmd: 其他参数(optional)
            specify_task_id: 自定义任务 ID(optional)
            comment: 任务描述(optional)
            to_url: 完整目标 URL 地址(optional)
            file_index: 指定播放文件索引(optional)
            offset_time: 指定播放文件偏移(optional)
            backup_source_type: 备源的类型(optional)
            backup_source_url: 备源 URL(optional)
            vod_local_mode: 点播源是否启用本地推流模式(optional)
            record_template_id: 录制模板 ID(optional)
            backup_to_url: 新的目标地址，用于任务同时推两路场景(optional)
            transcode_template_name: 直播转码模板(optional)

        Returns:
            TaskId: 任务ID
            请求ID
    """
    logger.info(f"创建直播拉流任务: region={region}, source_type={source_type},  source_urls={source_urls}, "
                f"domain_name={domain_name}, app_name={app_name}, stream_name={stream_name}, operator={operator}")

    try:
        live_client = LiveClient(region=region)
        result = live_client.create_live_pull_stream_task(
            source_type=source_type,
            source_urls=source_urls,
            domain_name=domain_name,
            app_name=app_name,
            stream_name=stream_name,
            start_time=start_time,
            end_time=end_time,
            operator=operator,
            push_args=push_args,
            callback_events=callback_events,
            vod_loop_times=vod_loop_times,
            vod_refresh_type=vod_refresh_type,
            callback_url=callback_url,
            extra_cmd=extra_cmd,
            specify_task_id=specify_task_id,
            comment=comment,
            to_url=to_url,
            file_index=file_index,
            offset_time=offset_time,
            backup_source_type=backup_source_type,
            backup_source_url=backup_source_url,
            vod_local_mode=vod_local_mode,
            record_template_id=record_template_id,
            backup_to_url=backup_to_url,
            transcode_template_name=transcode_template_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"创建直播拉流任务失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 更新直播拉流任务
@mcp.tool()
async def create_live_pull_stream_task(
        ctx: Context,
        region: str = Field(
            default=config.DEFAULT_REGION,
            description="地域"
        ),
        source_type: str = Field(
            default=None,
            description="拉流源的类型：PullLivePushLive -直播，PullVodPushLive -点播，PullPicPushLive -图片。示例值：PullLivePushLive"
        ),
        source_urls: List[str] = Field(
            default=None,
            description="拉流源 url 列表，SourceType 为直播（PullLivePushLive）只可以填1个，SourceType 为点播（PullVodPushLive）可以填多个，上限30个。当前支持的文件格式：flv，mp4，hls。当前支持的拉流协议：http，https，rtmp，rtmps，rtsp，srt。"
        ),
        domain_name: str = Field(
            default=None,
            description="推流域名。将拉取过来的流推到该域名"
        ),
        app_name: str = Field(
            default=None,
            description="推流路径。将拉取过来的流推到该路径。"
        ),
        stream_name: str = Field(
            default=None,
            description="推流名称。将拉取过来的流推到该流名称。"
        ),
        start_time: str = Field(
            default=None,
            description="开始时间。使用 UTC 格式时间，例如：2019-01-08T10:00:00Z"
        ),
        end_time: str = Field(
            default=None,
            description="结束时间"
        ),
        operator: str = Field(
            default=None,
            description="任务操作人备注"
        ),
        push_args: Optional[str] = Field(
            default=None,
            description="推流参数。推流时携带自定义参数。"
        ),
        callback_events: Optional[List[str]] = Field(
            default=None,
            description="选择需要回调的事件（不填则回调全部）"
        ),
        vod_loop_times: Optional[str] = Field(
            default=None,
            description="点播拉流转推循环次数，默认：-1"
        ),
        vod_refresh_type: Optional[str] = Field(
            default=None,
            description="点播更新SourceUrls后的播放方式：ImmediateNewSource：立即播放新的拉流源内容；ContinueBreakPoint：播放完当前正在播放的点播 url 后再使用新的拉流源播放。（旧拉流源未播放的点播 url 不会再播放）"
        ),
        callback_url: Optional[str] = Field(
            default=None,
            description="自定义回调地址。拉流转推任务相关事件会回调到该地址。"
        ),
        extra_cmd: Optional[str] = Field(
            default=None,
            description="其他参数"
        ),
        specify_task_id: Optional[str] = Field(
            default=None,
            description="自定义任务 ID"
        ),
        comment: Optional[str] = Field(
            default=None,
            description="任务描述，限制 512 字节"
        ),
        to_url: Optional[str] = Field(
            default=None,
            description="完整目标 URL 地址"
        ),
        file_index: Optional[int] = Field(
            default=None,
            description="指定播放文件索引"
        ),
        offset_time: Optional[int] = Field(
            default=None,
            description="指定播放文件偏移"
        ),
        backup_source_type: Optional[str] = Field(
            default=None,
            description="备源的类型：PullLivePushLive -直播，PullVodPushLive -点播"
        ),
        backup_source_url: Optional[str] = Field(
            default=None,
            description="备源 URL"
        ),
        vod_local_mode: Optional[int] = Field(
            default=None,
            description="点播源是否启用本地推流模式，默认0，不启用"
        ),
        record_template_id: Optional[str] = Field(
            default=None,
            description="录制模板 ID"
        ),
        backup_to_url: Optional[str] = Field(
            default=None,
            description="新的目标地址，用于任务同时推两路场景"
        ),
        transcode_template_name: Optional[str] = Field(
            default=None,
            description="直播转码模板，使用云直播的转码功能进行转码后再转推出去。转码模板需在云直播控制台创建"
        )
) -> str:
    """
    更新直播拉流任务

        Args:
            region: 地域
            source_type: 拉流源的类型
            source_urls: 拉流源 url 列表
            domain_name: 推流域名
            app_name: 推流路径
            stream_name: 推流名称
            start_time: 开始时间
            end_time: 结束时间
            operator: 任务操作人备注
            push_args: 推流参数(optional)
            callback_events: 需要回调的事件(optional)
            vod_loop_times: 点播拉流转推循环次数(optional)
            vod_refresh_type: 点播更新SourceUrls后的播放方式(optional)
            callback_url: 自定义回调地址(optional)
            extra_cmd: 其他参数(optional)
            specify_task_id: 自定义任务 ID(optional)
            comment: 任务描述(optional)
            to_url: 完整目标 URL 地址(optional)
            file_index: 指定播放文件索引(optional)
            offset_time: 指定播放文件偏移(optional)
            backup_source_type: 备源的类型(optional)
            backup_source_url: 备源 URL(optional)
            vod_local_mode: 点播源是否启用本地推流模式(optional)
            record_template_id: 录制模板 ID(optional)
            backup_to_url: 新的目标地址，用于任务同时推两路场景(optional)
            transcode_template_name: 直播转码模板(optional)

        Returns:
            TaskId: 任务ID
            请求ID
    """
    logger.info(f"更新直播拉流任务: region={region}, source_type={source_type},  source_urls={source_urls}, "
                f"domain_name={domain_name}, app_name={app_name}, stream_name={stream_name}, operator={operator}")

    try:
        live_client = LiveClient(region=region)
        result = live_client.create_live_pull_stream_task(
            source_type=source_type,
            source_urls=source_urls,
            domain_name=domain_name,
            app_name=app_name,
            stream_name=stream_name,
            start_time=start_time,
            end_time=end_time,
            operator=operator,
            push_args=push_args,
            callback_events=callback_events,
            vod_loop_times=vod_loop_times,
            vod_refresh_type=vod_refresh_type,
            callback_url=callback_url,
            extra_cmd=extra_cmd,
            specify_task_id=specify_task_id,
            comment=comment,
            to_url=to_url,
            file_index=file_index,
            offset_time=offset_time,
            backup_source_type=backup_source_type,
            backup_source_url=backup_source_url,
            vod_local_mode=vod_local_mode,
            record_template_id=record_template_id,
            backup_to_url=backup_to_url,
            transcode_template_name=transcode_template_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"更新直播拉流任务失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# <---------------------直播流管理---------------------> #
# 查询流状态
@mcp.tool()
async def describe_live_stream_state(
        ctx: Context,
        app_name: str = Field(
            default="live",
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        )
) -> str:
    """
    查询流状态
        Args:
            app_name: 推流路径
            domain_name: 推流域名
            stream_name: 流名称

        Returns:
            流状态
    """
    logger.info(f"查询流状态: app_name={app_name}, domain_name={domain_name}, stream_name={stream_name}")

    try:
        live_client = LiveClient()
        result = live_client.describe_live_stream_state(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"查询流状态失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 查询直播中的流
@mcp.tool()
async def describe_live_stream_online_list(
        ctx: Context,
        app_name: Optional[str] = Field(
            default="live",
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: Optional[str] = Field(
            default="5000.livepush.myqcloud.com",
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        page_num: Optional[int] = Field(
            default=1,
            description="取得第几页，默认1。示例值：1"
        ),
        page_size: Optional[int] = Field(
            default=10,
            description="每页大小，最大100。取值：10~100之间的任意整数。默认值：10。示例值：10"
        ),
        stream_name: Optional[str] = Field(
            default="mystream",
            description="流名称。示例值：stream1"
        )
) -> str:
    """
    查询直播中的流

        Args:
            app_name: 推流路径(optional)
            domain_name: 推流域名(optional)
            page_num: 取的第几页(optional)
            page_size: 每页大小(optional)
            stream_name: 流名称(optional)

        Returns:
            正在直播中的流列表
    """
    logger.info(f"查询直播中的流: app_name={app_name}, domain_name={domain_name},page_num={page_num},"
                f"page_size{page_size},stream_name={stream_name}")

    try:
        live_client = LiveClient()
        result = live_client.describe_live_stream_online_list(
            app_name=app_name,
            domain_name=domain_name,
            page_num=page_num,
            page_size=page_size,
            stream_name=stream_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"查询直播中的流失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# <---------------------流管理---------------------> #
# 断开直播流
@mcp.tool()
async def drop_live_stream(
        ctx: Context,
        app_name: str = Field(
            default=None,
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        )
) -> str:
    """
    断开直播流

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径

        Returns:
            请求ID
    """
    logger.info(f"断开直播推流: app_name={app_name}, domain_name={domain_name},stream_name={stream_name}")

    try:
        live_client = LiveClient()
        result = live_client.drop_live_stream(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"断开直播流失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 恢复直播流
@mcp.tool()
async def resume_live_stream(
        ctx: Context,
        app_name: str = Field(
            default=None,
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        )
) -> str:
    """
    恢复直播流

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径

        Returns:
            请求ID
    """
    logger.info(f"恢复直播流: app_name={app_name}, domain_name={domain_name},stream_name={stream_name}")

    try:
        live_client = LiveClient()
        result = live_client.resume_live_stream(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"断开直播流失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 禁推直播流
@mcp.tool()
async def forbid_live_stream(
        ctx: Context,
        app_name: str = Field(
            default=None,
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        ),
        resume_time: Optional[str] = Field(
            default=None,
            description="恢复流的时间。UTC 格式，例如：2018-11-29T19:00:00Z"
        ),
        reason: Optional[str] = Field(
            default=None,
            description="禁推原因。注明：请务必填写禁推原因，防止误操作"
        )
) -> str:
    """
    禁推直播流

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径
            resume_time: 恢复流的时间(optional)
            reason: 禁推原因(optional)

        Returns:
            请求ID
    """
    logger.info(f"禁推直播流: app_name={app_name}, domain_name={domain_name},stream_name={stream_name}")

    try:
        live_client = LiveClient()
        result = live_client.forbid_live_stream(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name,
            resume_time=resume_time,
            reason=reason
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"禁推直播流失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 查询推断流事件
@mcp.tool()
async def describe_live_stream_event_list(
        ctx: Context,
        start_time: str = Field(
            default=None,
            description="起始时间。 UTC 格式，例如：2018-12-29T19:00:00Z。支持查询2个月内的历史记录"
        ),
        end_time: str = Field(
            default=None,
            description="结束时间。UTC 格式，例如：2018-12-29T20:00:00Z。不超过当前时间，且和起始时间相差不得超过1个月"
        ),
        app_name: Optional[str] = Field(
            default=None,
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: Optional[str] = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: Optional[str] = Field(
            default=None,
            description="流名称。示例值：stream1"
        ),
        page_num: Optional[int] = Field(
            default=None,
            description="取得第几页"
        ),
        page_size: Optional[int] = Field(
            default=None,
            description="分页大小"
        ),
        is_fiter: Optional[int] = Field(
            default=None,
            description="是否过滤，默认不过滤"
        ),
        is_strict: Optional[int] = Field(
            default=None,
            description="是否精确查询，默认模糊匹配"
        ),
        is_asc: Optional[int] = Field(
            default=None,
            description="是否按结束时间正序显示，默认逆序"
        )
) -> str:
    """
    查询推断流事件

        Args:
            start_time: 起始时间
            end_time: 结束时间
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径(optional)
            page_num: 取得第几页(optional)
            page_size: 分页大小(optional)
            is_fiter: 是否过滤(optional)
            is_strict: 是否精确查询(optional)
            is_asc: 是否按结束时间正序显示(optional)

        Returns:
            EventList: 推断流事件列表
            PageNum: 分页的页码
            PageSize: 每页大小
            TotalNum: 符合条件的总个数
            TotalPage: 总页数
            请求ID
    """
    logger.info(f"查询推断流事件: start_time={start_time}, end_time={end_time}")

    try:
        live_client = LiveClient()
        result = live_client.describe_live_stream_event_list(
            start_time=start_time,
            end_time=end_time,
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name,
            page_num=page_num,
            page_size=page_size,
            is_fiter=is_fiter,
            is_strict=is_strict,
            is_asc=is_asc
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"查询推断流事件失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 设置延时直播
@mcp.tool()
async def add_delay_live_stream(
        ctx: Context,
        app_name: str = Field(
            default=None,
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        ),
        delay_time: str = Field(
            default=None,
            description="延播时间，单位：秒，上限：600秒"
        ),
        expire_time: Optional[str] = Field(
            default=None,
            description="延播设置的过期时间。UTC 格式，例如：2018-11-29T19:00:00Z"
        )
) -> str:
    """
    设置延时直播

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径
            delay_time: 延播时间
            expire_time: 延播设置的过期时间(optional)

        Returns:
            请求ID
    """
    logger.info(f"设置延时直播: app_name={app_name}, domain_name={domain_name},"
                f"stream_name={stream_name},delay_time={delay_time}")

    try:
        live_client = LiveClient()
        result = live_client.add_delay_live_stream(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name,
            delay_time=delay_time,
            expire_time=expire_time
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"设置延时直播失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 取消直播延时
@mcp.tool()
async def resume_delay_live_stream(
        ctx: Context,
        app_name: str = Field(
            default=None,
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        )
) -> str:
    """
    取消直播延时

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径

        Returns:
            请求ID
    """
    logger.info(f"取消直播延时: app_name={app_name}, domain_name={domain_name},stream_name={stream_name}")

    try:
        live_client = LiveClient()
        result = live_client.resume_delay_live_stream(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"取消直播延时失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# <---------------------转码模版---------------------> #
# 创建转码模板
@mcp.tool()
async def create_live_transcode_template(
        ctx: Context,
        template_name: str = Field(
            default=None,
            description="模板名称，例: 900p 仅支持字母和数字的组合"
        ),
        video_bitrate: int = Field(
            default=None,
            description="视频码率。范围：0kbps - 8000kbps"
        ),
        acodec: Optional[str] = Field(
            default=None,
            description="音频编码：aac，默认aac"
        ),
        audio_bitrate: Optional[int] = Field(
            default=None,
            description="音频码率，默认0"
        ),
        vcodec: Optional[str] = Field(
            default=None,
            description="视频编码：h264/h265/origin，默认origin"
        ),
        description: Optional[str] = Field(
            default=None,
            description="模板描述"
        ),
        need_video: Optional[int] = Field(
            default=None,
            description="是否保留视频，0：否，1：是。默认1"
        ),
        width: Optional[int] = Field(
            default=None,
            description="宽，默认0。范围[0-3000] 数值必须是2的倍数，0是原始宽度"
        ),
        need_audio: Optional[int] = Field(
            default=None,
            description="是否保留音频，0：否，1：是。默认1"
        ),
        height: Optional[int] = Field(
            default=None,
            description="高，默认0。范围[0-3000] 数值必须是2的倍数，0是原始高度"
        ),
        fps: Optional[int] = Field(
            default=None,
            description="帧率，默认0。范围0-60fps"
        ),
        gop: Optional[int] = Field(
            default=None,
            description="关键帧间隔，单位：秒。默认原始的间隔范围2-6"
        ),
        rotate: Optional[int] = Field(
            default=None,
            description="旋转角度，默认0 可取值：0，90，180，270"
        ),
        profile: Optional[str] = Field(
            default=None,
            description="编码质量：baseline/main/high。默认baseline"
        ),
        bitrate_to_orig: Optional[int] = Field(
            default=None,
            description="当设置的码率>原始码率时，是否以原始码率为准。0：否， 1：是"
        ),
        height_to_orig: Optional[int] = Field(
            default=None,
            description="当设置的高度>原始高度时，是否以原始高度为准。0：否， 1：是"
        ),
        fps_to_orig: Optional[int] = Field(
            default=None,
            description="当设置的帧率>原始帧率时，是否以原始帧率为准。0：否， 1：是"
        ),
        ai_trans_code: Optional[int] = Field(
            default=None,
            description="是否是极速高清模板，0：否，1：是。默认0"
        ),
        adapt_bitrate_percent: Optional[float] = Field(
            default=None,
            description="极速高清视频码率压缩比"
        ),
        short_edge_as_height: Optional[int] = Field(
            default=None,
            description="是否以短边作为高度，0：否，1：是。默认0"
        ),
        drm_type: Optional[str] = Field(
            default=None,
            description="DRM 加密类型，可选值：fairplay、normalaes、widevine"
        ),
        drm_tracks: Optional[str] = Field(
            default=None,
            description="DRM 加密项，可选值：AUDIO、SD、HD、UHD1、UHD2，后四个为一组，同组中的内容只能选一个"
        )
) -> str:
    """
    创建转码模板

        Args:
            template_name: 模板名称
            video_bitrate: 视频码率
            acodec: 音频编码(optional)
            audio_bitrate: 音频码率(optional)
            vcodec: 视频编码(optional)
            description: 模板描述(optional)
            need_video: 是否保留视频(optional)
            width: 宽(optional)
            need_audio: 是否保留音频(optional)
            height: 高(optional)
            fps: 帧率(optional)
            gop: 关键帧间隔(optional)
            rotate: 旋转角度(optional)
            profile: 编码质量(optional)
            bitrate_to_orig: 当设置的码率>原始码率时，是否以原始码率为准(optional)
            height_to_orig: 当设置的高度>原始高度时，是否以原始高度为准(optional)
            fps_to_orig: 当设置的帧率>原始帧率时，是否以原始帧率为准(optional)
            ai_trans_code: 是否是极速高清模板(optional)
            adapt_bitrate_percent: 极速高清视频码率压缩比(optional)
            short_edge_as_height: 是否以短边作为高度(optional)
            drm_type: DRM 加密类型(optional)
            drm_tracks: DRM 加密项(optional)

        Returns:
            TemplateId: 模版ID
            请求ID
    """
    logger.info(f"创建转码模板: template_name={template_name}, video_bitrate={video_bitrate}")

    try:
        live_client = LiveClient()
        result = live_client.create_live_transcode_template(
            template_name=template_name,
            video_bitrate=video_bitrate,
            acodec=acodec,
            audio_bitrate=audio_bitrate,
            vcodec=vcodec,
            description=description,
            need_video=need_video,
            width=width,
            need_audio=need_audio,
            height=height,
            fps=fps,
            gop=gop,
            rotate=rotate,
            profile=profile,
            bitrate_to_orig=bitrate_to_orig,
            height_to_orig=height_to_orig,
            fps_to_orig=fps_to_orig,
            ai_trans_code=ai_trans_code,
            adapt_bitrate_percent=adapt_bitrate_percent,
            short_edge_as_height=short_edge_as_height,
            drm_type=drm_type,
            drm_tracks=drm_tracks
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"创建转码模板失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 删除转码模板
@mcp.tool()
async def delete_live_transcode_template(
        ctx: Context,
        template_id: int,
) -> str:
    """
    删除转码模板

        Args:
            template_id: 模版ID

        Returns:
            请求ID
    """
    logger.info(f"删除转码模板: template_id={template_id}")

    try:
        live_client = LiveClient()
        result = live_client.delete_live_transcode_template(
            template_id=template_id,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"删除转码模板失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 创建转码规则
@mcp.tool()
async def create_live_transcode_rule(
        ctx: Context,
        app_name: str = Field(
            default="live",
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        ),
        template_id: int = Field(
            default=None,
            description="模版ID"
        )
) -> str:
    """
    创建转码规则
        Args:
            app_name: 推流路径
            domain_name: 推流域名
            stream_name: 流名称
            template_id: 模版ID

        Returns:
            请求ID
    """
    logger.info(f"创建转码规则: app_name={app_name}, domain_name={domain_name}, "
                f"stream_name={stream_name}, template_id={template_id}")

    try:
        live_client = LiveClient()
        result = live_client.create_live_transcode_rule(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name,
            template_id=template_id
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"创建转码规则失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


# 删除转码规则
@mcp.tool()
async def delete_live_transcode_rule(
        ctx: Context,
        app_name: str = Field(
            default="live",
            description="推流路径，与推流和播放地址中的AppName保持一致，默认为live"
        ),
        domain_name: str = Field(
            default=None,
            description="您的推流域名。示例值：5000.livepush.myqcloud.com"
        ),
        stream_name: str = Field(
            default=None,
            description="流名称。示例值：stream1"
        ),
        template_id: int = Field(
            default=None,
            description="模版ID"
        )
) -> str:
    """
    删除转码规则
        Args:
            app_name: 推流路径
            domain_name: 推流域名
            stream_name: 流名称
            template_id: 模版ID

        Returns:
            请求ID
    """
    logger.info(f"删除转码规则: app_name={app_name}, domain_name={domain_name}, "
                f"stream_name={stream_name}, template_id={template_id}")

    try:
        live_client = LiveClient()
        result = live_client.delete_live_transcode_rule(
            app_name=app_name,
            domain_name=domain_name,
            stream_name=stream_name,
            template_id=template_id
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"删除转码规则失败: {e}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg}, ensure_ascii=False)


def main():
    """运行MCP服务器，支持命令行参数。"""
    parser = argparse.ArgumentParser(
        description='腾讯云API的模型上下文协议(MCP)服务器'
    )
    parser.add_argument('--transport', type=str, default='stdio', choices=['sse', 'stdio'],
                        help='传输模式，可选值：sse(服务器发送事件)或stdio(标准输入输出)，默认为sse')
    parser.add_argument('--port', type=int, default=9000, help='服务器运行端口')

    args = parser.parse_args()

    # 记录启动信息
    logger.info('启动腾讯云API MCP服务器')
    logger.info(f'TENCENT_SECRET_ID:{config.SECRET_ID}, TENCENT_SECRET_KEY:{config.SECRET_KEY}')

    # 根据传输方式运行服务器
    if args.transport == 'stdio':
        logger.info('使用标准输入输出传输')
        mcp.run()
    else:
        logger.info(f'使用SSE传输，端口: {args.port}')
        mcp.settings.port = args.port
        mcp.run(transport='sse')


if __name__ == "__main__":
    main()
