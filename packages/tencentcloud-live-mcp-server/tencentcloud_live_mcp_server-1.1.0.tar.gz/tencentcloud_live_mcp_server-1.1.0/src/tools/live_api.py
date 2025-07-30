#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@File    : live_api.py
@Time    : 2025/05/30
@Author  : willsygao
@Desc    : 提供腾讯云直播api相关功能
"""

from typing import Dict, Any, List, Optional

from utils.config import config
from utils.tencent_client import TencentCloudClient
from utils.logger import setup_logger

logger = setup_logger("live_api")


class LiveClient(TencentCloudClient):
    """Live API 客户端"""

    def __init__(self, region: Optional[str] = None):
        """
        初始化Live API客户端
        Args:
            region: 区域，默认使用配置中的区域
        """
        super().__init__(
            service="live",
            version=config.LIVE_API_VERSION,
            endpoint=config.LIVE_ENDPOINT,
            region=region
        )

    # <---------------------获取推流地址---------------------> #
    def describe_live_push_auth_key(
            self,
            domain_name: str,
    ) -> Dict[str, Any]:
        """
        获取推流地址
        Args:
            domain_name: 推流域名

        Returns:
            PushAuthKeyInfo: 推流鉴权key信息
            请求ID
        """
        params = {
            "DomainName": domain_name
        }

        return self.call_api("DescribeLivePushAuthKey", params)

    # <---------------------获取播放地址---------------------> #
    def describe_live_play_auth_key(
            self,
            domain_name: str,
    ) -> Dict[str, Any]:
        """
        获取播放地址
        Args:
            domain_name: 推流域名

        Returns:
            PlayAuthKeyInfo: 推流鉴权key信息
            请求ID
        """
        params = {
            "DomainName": domain_name
        }

        return self.call_api("DescribeLivePlayAuthKey", params)

    # <---------------------域名管理---------------------> #
    # 添加域名
    def add_live_domain(
            self,
            domain_name: str,
            domain_type: int,
            play_type: Optional[int],
            is_delay_live: Optional[int],
            is_mini_program_live: Optional[int],
            verify_owner_type: Optional[str]
    ) -> Dict[str, Any]:
        """
        添加域名

        Args:
            domain_name: 推流域名
            domain_type: 域名类型
            play_type: 拉流域名类型
            is_delay_live: 是否是慢直播
            is_mini_program_live: 是否是小程序直播
            verify_owner_type: 域名归属校验类型

        Returns:
            请求ID
        """
        params = {
            "DomainName": domain_name,
            "DomainType": domain_type
        }
        if play_type:
            params["PlayType"] = play_type

        if is_delay_live:
            params["IsDelayLive"] = is_delay_live

        if is_mini_program_live:
            params["IsMiniProgramLive"] = is_mini_program_live

        if verify_owner_type:
            params["VerifyOwnerType"] = verify_owner_type

        return self.call_api("AddLiveDomain", params)

    # 删除域名
    def delete_live_domain(
            self,
            domain_name: str,
            domain_type: int
    ) -> Dict[str, Any]:
        """
        删除域名
        Args:
            domain_name: 推流域名
            domain_type: 域名类型

        Returns:
            请求ID
        """
        params = {
            "DomainName": domain_name,
            "DomainType": domain_type
        }

        return self.call_api("DeleteLiveDomain", params)

    # 启用域名
    def enable_live_domain(
            self,
            domain_name: str
    ) -> Dict[str, Any]:
        """
        删除域名
        Args:
            domain_name: 推流域名

        Returns:
            请求ID
        """
        params = {
            "DomainName": domain_name
        }

        return self.call_api("EnableLiveDomain", params)

    # 禁用域名
    def forbid_live_domain(
            self,
            domain_name: str
    ) -> Dict[str, Any]:
        """
        删除域名
        Args:
            domain_name: 推流域名

        Returns:
            请求ID
        """
        params = {
            "DomainName": domain_name
        }

        return self.call_api("ForbidLiveDomain", params)

    # 查询域名信息
    def describe_live_domain(
            self,
            domain_name: str
    ) -> Dict[str, Any]:
        """
        查询域名信息
        Args:
            domain_name: 推流域名

        Returns:
            请求ID
        """
        params = {
            "DomainName": domain_name
        }

        return self.call_api("DescribeLiveDomain", params)

    # 查询域名列表
    def describe_live_domains(
            self,
            domain_status: Optional[int],
            domain_type: Optional[int],
            page_size: Optional[int],
            page_num: Optional[int],
            is_delay_live: Optional[int],
            domain_prefix: Optional[str],
            play_type: Optional[int]
    ) -> Dict[str, Any]:
        """
        查询域名列表

        Args:
            domain_status: 域名状态过滤
            domain_type: 域名类型
            page_size: 分页大小
            page_num: 取第几页
            is_delay_live: 普通直播/慢直播
            domain_prefix: 域名前缀
            play_type: 播放区域

        Returns:
            AllCount: 总记录数
            DomainList: 域名详细信息列表
            CreateLimitCount: 可继续添加域名数量
            PlayTypeCount: 启用的播放域名加速区域统计
            请求ID
        """
        params = {}
        if domain_status:
            params["DomainStatus"] = domain_status

        if domain_type:
            params["DomainType"] = domain_type

        if page_size:
            params["PageSize"] = page_size

        if page_num:
            params["PageNum"] = page_num

        if is_delay_live:
            params["IsDelayLive"] = is_delay_live

        if play_type:
            params["PlayType"] = play_type

        if domain_prefix:
            params["DomainPrefix"] = domain_prefix

        return self.call_api("DescribeLiveDomains", params)

    # <---------------------拉流转推---------------------> #
    # 删除直播拉流任务
    def delete_live_pull_stream_task(
            self,
            task_id: str,
            operator: str,
            specify_task_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        删除直播拉流任务

        Args:
            task_id: 任务ID
            operator: 操作人姓名
            specify_task_id: 指定任务ID

        Returns:
            请求ID
        """
        params = {
            "TaskId": task_id,
            "Operator": operator
        }

        if specify_task_id:
            params["SpecifyTaskId"] = specify_task_id

        return self.call_api("DeleteLivePullStreamTask", params)

    # 查询直播拉流任务
    def describe_live_pull_stream_tasks(
            self,
            task_id: Optional[str],
            page_num: Optional[int],
            page_size: Optional[int],
            specify_task_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        删除直播拉流任务

        Args:
            task_id: 任务ID
            page_num: 取得第几页
            page_size: 分页大小
            specify_task_id: 指定任务ID

        Returns:
            TaskInfos: 直播拉流任务信息列表
            PageNum: 分页的页码
            PageSize: 每页大小
            TotalNum: 符合条件的总个数
            TotalPage: 总页数
            LimitTaskNum: 限制可创建的最大任务数
            请求ID
        """
        params = {}

        if task_id:
            params["TaskId"] = task_id

        if page_num:
            params["PageNum"] = page_num

        if page_size:
            params["PageSize"] = page_size

        if specify_task_id:
            params["SpecifyTaskId"] = specify_task_id

        return self.call_api("DescribeLivePullStreamTasks", params)

    # 创建直播拉流任务
    def create_live_pull_stream_task(
            self,
            source_type: str,
            source_urls: List[str],
            domain_name: str,
            app_name: str,
            stream_name: str,
            start_time: str,
            end_time: str,
            operator: str,
            push_args: Optional[str],
            callback_events: Optional[List[str]],
            vod_loop_times: Optional[str],
            vod_refresh_type: Optional[str],
            callback_url: Optional[str],
            extra_cmd: Optional[str],
            specify_task_id: Optional[str],
            comment: Optional[str],
            to_url: Optional[str],
            file_index: Optional[int],
            offset_time: Optional[int],
            backup_source_type: Optional[str],
            backup_source_url: Optional[str],
            vod_local_mode: Optional[int],
            record_template_id: Optional[str],
            backup_to_url: Optional[str],
            transcode_template_name: Optional[str]
    ) -> Dict[str, Any]:
        """
        创建直播拉流任务

        Args:
            source_type: 拉流源的类型
            source_urls: 拉流源 url 列表
            domain_name: 推流域名
            app_name: 推流路径
            stream_name: 推流名称
            start_time: 开始时间
            end_time: 结束时间
            operator: 任务操作人备注
            push_args: 推流参数
            callback_events: 需要回调的事件
            vod_loop_times: 点播拉流转推循环次数
            vod_refresh_type: 点播更新SourceUrls后的播放方式
            callback_url: 自定义回调地址
            extra_cmd: 其他参数
            specify_task_id: 自定义任务 ID
            comment: 任务描述
            to_url: 完整目标 URL 地址
            file_index: 指定播放文件索引
            offset_time: 指定播放文件偏移
            backup_source_type: 备源的类型
            backup_source_url: 备源 URL
            vod_local_mode: 点播源是否启用本地推流模式
            record_template_id: 录制模板 ID
            backup_to_url: 新的目标地址，用于任务同时推两路场景
            transcode_template_name: 直播转码模板

        Returns:
            TaskId: 任务ID
            请求ID
        """
        params = {
            "SourceType": source_type,
            "SourceUrls": source_urls,
            "DomainName": domain_name,
            "AppName": app_name,
            "StreamName": stream_name,
            "StartTime": start_time,
            "EndTime": end_time,
            "Operator": operator,
        }

        if push_args:
            params["PushArgs"] = push_args

        if callback_events:
            params["CallbackEvents"] = callback_events

        if vod_loop_times:
            params["VodLoopTimes"] = vod_loop_times

        if vod_refresh_type:
            params["VodRefreshType"] = vod_refresh_type

        if callback_url:
            params["CallbackUrl"] = callback_url

        if extra_cmd:
            params["ExtraCmd"] = extra_cmd

        if specify_task_id:
            params["SpecifyTaskId"] = specify_task_id

        if comment:
            params["Comment"] = comment

        if to_url:
            params["ToUrl"] = to_url

        if file_index:
            params["FileIndex"] = file_index

        if offset_time:
            params["OffsetTime"] = offset_time

        if backup_source_type:
            params["BackupSourceType"] = backup_source_type

        if backup_source_url:
            params["BackupSourceUrl"] = backup_source_url

        if vod_local_mode:
            params["VodLocalMode"] = vod_local_mode

        if record_template_id:
            params["RecordTemplateId"] = record_template_id

        if backup_to_url:
            params["BackupToUrl"] = backup_to_url

        if transcode_template_name:
            params["TranscodeTemplateName"] = transcode_template_name

        return self.call_api("CreateLivePullStreamTask", params)

    # 更新直播拉流任务
    def modify_live_pull_stream_task(
            self,
            task_id: str,
            operator: str,
            source_urls: Optional[List[str]],
            start_time: Optional[str],
            end_time: Optional[str],
            vod_loop_times: Optional[int],
            vod_refresh_type: Optional[str],
            status: Optional[str],
            callback_events: Optional[List[str]],
            callback_url: Optional[str],
            specify_task_id: Optional[str],
            comment: Optional[str],
            to_url: Optional[str],
            file_index: Optional[int],
            offset_time: Optional[int],
            backup_source_type: Optional[str],
            backup_source_url: Optional[str],
            vod_local_mode: Optional[int],
            backup_to_url: Optional[str],
            backup_vod_url: Optional[str]
    ) -> Dict[str, Any]:
        """
        更新直播拉流任务

        Args:
            task_id: 任务Id
            source_urls: 拉流源 url 列表
            start_time: 开始时间
            end_time: 结束时间
            operator: 任务操作人备注
            callback_events: 需要回调的事件
            vod_loop_times: 点播拉流转推循环次数
            vod_refresh_type: 点播更新SourceUrls后的播放方式
            status: 任务状态
            callback_url: 自定义回调地址
            specify_task_id: 自定义任务 ID
            comment: 任务描述
            to_url: 完整目标 URL 地址
            file_index: 指定播放文件索引
            offset_time: 指定播放文件偏移
            backup_source_type: 备源的类型
            backup_source_url: 备源 URL
            vod_local_mode: 点播源是否启用本地推流模式
            backup_to_url: 新的目标地址，用于任务同时推两路场景
            backup_vod_url: 点播垫片文件地址

        Returns:
            请求ID
        """
        params = {
            "TaskId": task_id,
            "Operator": operator
        }

        if source_urls:
            params["SourceUrls"] = source_urls

        if start_time:
            params["StartTime"] = start_time

        if end_time:
            params["EndTime"] = end_time

        if callback_events:
            params["CallbackEvents"] = callback_events

        if vod_loop_times:
            params["VodLoopTimes"] = vod_loop_times

        if vod_refresh_type:
            params["VodRefreshType"] = vod_refresh_type

        if callback_url:
            params["CallbackUrl"] = callback_url

        if specify_task_id:
            params["SpecifyTaskId"] = specify_task_id

        if comment:
            params["Comment"] = comment

        if to_url:
            params["ToUrl"] = to_url

        if file_index:
            params["FileIndex"] = file_index

        if offset_time:
            params["OffsetTime"] = offset_time

        if backup_source_type:
            params["BackupSourceType"] = backup_source_type

        if backup_source_url:
            params["BackupSourceUrl"] = backup_source_url

        if vod_local_mode:
            params["VodLocalMode"] = vod_local_mode

        if backup_to_url:
            params["BackupToUrl"] = backup_to_url

        if status:
            params["Status"] = status

        if backup_vod_url:
            params["BackupVodUrl"] = backup_vod_url

        return self.call_api("ModifyLivePullStreamTask", params)

    # <---------------------直播流管理---------------------> #
    # 查询流状态
    def describe_live_stream_state(
            self,
            app_name: str,
            domain_name: str,
            stream_name: str
    ) -> Dict[str, Any]:
        """
        查询流状态

        Args:
            app_name: 推流路径
            domain_name: 推流域名
            stream_name: 流名称

        Returns:
            流状态
        """
        params = {
            "AppName": app_name,
            "DomainName": domain_name,
            "StreamName": stream_name
        }

        return self.call_api("DescribeLiveStreamState", params)

    # 查询直播中的流
    def describe_live_stream_online_list(
            self,
            app_name: Optional[str],
            domain_name: Optional[str],
            page_num: Optional[int],
            page_size: Optional[int],
            stream_name: Optional[str]
    ) -> Dict[str, Any]:
        """
        查询直播中的流

        Args:
            app_name: 推流路径
            domain_name: 推流域名
            page_num: 取的第几页
            page_size: 每页大小
            stream_name: 流名称

        Returns:
            正在直播中的流列表
        """
        params = {}

        if app_name:
            params["AppName"] = app_name

        if domain_name:
            params["DomainName"] = domain_name

        if page_num:
            params["PageNumber"] = page_num

        if page_size:
            params["PageSize"] = page_size

        if stream_name:
            params["StreamName"] = stream_name

        return self.call_api("DescribeLiveStreamOnlineList", params)

    # <---------------------流管理---------------------> #
    # 断开直播推流
    def drop_live_stream(
            self,
            stream_name: str,
            domain_name: str,
            app_name: str
    ) -> Dict[str, Any]:
        """
        断开直播推流

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径

        Returns:
            请求ID
        """
        params = {
            "StreamName": stream_name,
            "DomainName": domain_name,
            "AppName": app_name
        }

        return self.call_api("DropLiveStream", params)

    # 恢复直播流
    def resume_live_stream(
            self,
            stream_name: str,
            domain_name: str,
            app_name: str
    ) -> Dict[str, Any]:
        """
        恢复直播流

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径

        Returns:
            请求ID
        """
        params = {
            "StreamName": stream_name,
            "DomainName": domain_name,
            "AppName": app_name
        }

        return self.call_api("ResumeLiveStream", params)

    # 禁推直播流
    def forbid_live_stream(
            self,
            stream_name: str,
            domain_name: str,
            app_name: str,
            resume_time: Optional[str],
            reason: Optional[str],
    ) -> Dict[str, Any]:
        """
        禁推直播流

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径
            resume_time: 恢复流的时间
            reason: 禁推原因

        Returns:
            请求ID
        """
        params = {
            "StreamName": stream_name,
            "DomainName": domain_name,
            "AppName": app_name
        }

        if resume_time:
            params["ResumeTime"] = resume_time

        if reason:
            params["Reason"] = reason

        return self.call_api("ForbidLiveStream", params)

    # 查询推断流事件
    def describe_live_stream_event_list(
            self,
            start_time: str,
            end_time: str,
            app_name: Optional[str],
            domain_name: Optional[str],
            stream_name: Optional[str],
            page_num: Optional[int],
            page_size: Optional[int],
            is_fiter: Optional[int],
            is_strict: Optional[int],
            is_asc: Optional[int]
    ) -> Dict[str, Any]:
        """
        查询推断流事件

        Args:
            start_time: 起始时间
            end_time: 结束时间
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径
            page_num: 取得第几页
            page_size: 分页大小
            is_fiter: 是否过滤
            is_strict: 是否精确查询
            is_asc: 是否按结束时间正序显示

        Returns:
            EventList: 推断流事件列表
            PageNum: 分页的页码
            PageSize: 每页大小
            TotalNum: 符合条件的总个数
            TotalPage: 总页数
            请求ID
        """
        params = {
            "StartTime": start_time,
            "EndTime": end_time
        }

        if stream_name:
            params["StreamName"] = stream_name

        if domain_name:
            params["DomainName"] = domain_name

        if app_name:
            params["AppName"] = app_name

        if page_num:
            params["PageNumber"] = page_num

        if page_size:
            params["PageSize"] = page_size

        if is_fiter:
            params["IsFiter"] = is_fiter

        if is_strict:
            params["IsStrict"] = is_strict

        if is_asc:
            params["IsAsc"] = is_asc

        return self.call_api("DescribeLiveStreamEventList", params)

    # 设置延时直播
    def add_delay_live_stream(
            self,
            stream_name: str,
            domain_name: str,
            app_name: str,
            delay_time: str,
            expire_time: Optional[str]
    ) -> Dict[str, Any]:
        """
        设置延时直播

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径
            delay_time: 延播时间
            expire_time: 延播设置的过期时间

        Returns:
            请求ID
        """
        params = {
            "StreamName": stream_name,
            "DomainName": domain_name,
            "AppName": app_name,
            "DelayTime": delay_time,
        }

        if expire_time:
            params["ExpireTime"] = expire_time

        return self.call_api("AddDelayLiveStream", params)

    # 取消直播延时
    def resume_delay_live_stream(
            self,
            stream_name: str,
            domain_name: str,
            app_name: str
    ) -> Dict[str, Any]:
        """
        取消直播延时

        Args:
            stream_name: 流名称
            domain_name: 推流域名
            app_name: 推流路径

        Returns:
            请求ID
        """
        params = {
            "StreamName": stream_name,
            "DomainName": domain_name,
            "AppName": app_name
        }

        return self.call_api("ResumeLiveStream", params)

    # <---------------------转码模版---------------------> #
    # 创建转码模板
    def create_live_transcode_template(
            self,
            template_name: str,
            video_bitrate: int,
            acodec: Optional[str],
            audio_bitrate: Optional[int],
            vcodec: Optional[str],
            description: Optional[str],
            need_video: Optional[int],
            width: Optional[int],
            need_audio: Optional[int],
            height: Optional[int],
            fps: Optional[int],
            gop: Optional[int],
            rotate: Optional[int],
            profile: Optional[str],
            bitrate_to_orig: Optional[int],
            height_to_orig: Optional[int],
            fps_to_orig: Optional[int],
            ai_trans_code: Optional[int],
            adapt_bitrate_percent: Optional[float],
            short_edge_as_height: Optional[int],
            drm_type: Optional[str],
            drm_tracks: Optional[str]
    ) -> Dict[str, Any]:
        """
        创建转码模板

        Args:
            template_name: 模板名称
            video_bitrate: 视频码率
            acodec: 音频编码
            audio_bitrate: 音频码率
            vcodec: 视频编码
            description: 模板描述
            need_video: 是否保留视频
            width: 宽
            need_audio: 是否保留音频
            height: 高
            fps: 帧率
            gop: 关键帧间隔
            rotate: 旋转角度
            profile: 编码质量
            bitrate_to_orig: 当设置的码率>原始码率时，是否以原始码率为准
            height_to_orig: 当设置的高度>原始高度时，是否以原始高度为准
            fps_to_orig: 当设置的帧率>原始帧率时，是否以原始帧率为准
            ai_trans_code: 是否是极速高清模板
            adapt_bitrate_percent: 极速高清视频码率压缩比
            short_edge_as_height: 是否以短边作为高度
            drm_type: DRM 加密类型
            drm_tracks: DRM 加密项

        Returns:
            TemplateId: 模版ID
            请求ID
        """
        params = {
            "TemplateName": template_name,
            "VideoBitrate": video_bitrate
        }

        if acodec:
            params["Acodec"] = acodec

        if audio_bitrate:
            params["AudioBitrate"] = audio_bitrate

        if vcodec:
            params["Vcodec"] = vcodec

        if description:
            params["Description"] = description

        if need_video:
            params["NeedVideo"] = need_video

        if width:
            params["Width"] = width

        if need_audio:
            params["NeedAudio"] = need_audio

        if height:
            params["Height"] = height

        if fps:
            params["Fps"] = fps

        if gop:
            params["Gop"] = gop

        if rotate:
            params["Rotate"] = rotate

        if profile:
            params["Profile"] = profile

        if bitrate_to_orig:
            params["BitrateToOrigin"] = bitrate_to_orig

        if height_to_orig:
            params["HeightToOrigin"] = height_to_orig

        if fps_to_orig:
            params["FpsToOrigin"] = fps_to_orig

        if ai_trans_code:
            params["AiTransCode"] = ai_trans_code

        if adapt_bitrate_percent:
            params["AdaptBitratePercent"] = adapt_bitrate_percent

        if short_edge_as_height:
            params["ShortEdgeAsHeight"] = short_edge_as_height

        if drm_type:
            params["DRMType"] = drm_type

        if drm_tracks:
            params["DRMTracks"] = drm_tracks

        return self.call_api("CreateLiveTranscodeTemplate", params)

    # 删除转码模板
    def delete_live_transcode_template(
            self,
            template_id: int
    ) -> Dict[str, Any]:
        """
        删除转码模板

        Args:
            template_id: 模版ID

        Returns:
            请求ID
        """
        params = {
            "TemplateId": template_id
        }

        return self.call_api("DeleteLiveTranscodeTemplate", params)

    # 创建转码规则
    def create_live_transcode_rule(
            self,
            app_name: str,
            domain_name: str,
            stream_name: str,
            template_id: int
    ) -> Dict[str, Any]:
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
        params = {
            "AppName": app_name,
            "DomainName": domain_name,
            "StreamName": stream_name,
            "TemplateId": template_id
        }

        return self.call_api("CreateLiveTranscodeRule", params)

    # 删除转码规则
    def delete_live_transcode_rule(
            self,
            app_name: str,
            domain_name: str,
            stream_name: str,
            template_id: int
    ) -> Dict[str, Any]:
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
        params = {
            "AppName": app_name,
            "DomainName": domain_name,
            "StreamName": stream_name,
            "TemplateId": template_id
        }

        return self.call_api("DeleteLiveTranscodeRule", params)
