# 腾讯云直播服务

本服务基于Model Context Protocol（MCP）实现提供腾讯云直播API调用Tools的MCP Server，提供腾讯云直播域名管理、拉流转推、直播流管理和流管理等相关接口。

## 简介

本项目主要为大语言模型提供通过自然语言调用腾讯云直播API，管理腾讯云直播服务的能力。

## 依赖环境

- Python 1.12
- 腾讯云API密钥（ [腾讯云控制台申请](https://console.cloud.tencent.com/cam/capi) ）
    - TENCENTCLOUD_SECRET_ID
    - TENCENTCLOUD_SECRET_KEY
- 腾讯云SDK-Python

## 获取安装

### 本地运行Server

``` 
# 配置环境变量
export TENCENTCLOUD_SECRET_ID="您的腾讯云SecretId"
export TENCENTCLOUD_SECRET_KEY="您的腾讯云SecretId"

# 启动服务
uv run src/server.py
```
### Cursor中使用
#### 通过发布在PyPI的包使用

先决条件：[uv包管理器](https://docs.astral.sh/uv/getting-started/installation/)

需要注意的是，你必须安装好了uvx才可以进行Cursor的配置。

``` 
{
  "mcpServers": {
    "tencentcloud-live-mcp-server": {
      "command": "uvx",
      "args": [
        "tencentcloud-live-mcp-server"
      ],
      "env": {
        "TENCENTCLOUD_SECRET_ID": "------> 替换成你自己的 ID <------",
        "TENCENTCLOUD_SECRET_KEY": "------> 替换成你自己的 KEY <------"
      }
    }
  }
}
```
完成后重启Cursor完成配置。

## 功能
- Tools
    - 域名管理
        - 添加域名
        - 删除域名
        - 启用域名
        - 禁用域名
        - 查询域名信息
        - 查询域名列表
    - 拉流转推
        - 删除直播拉流任务
        - 查询直播拉流任务
        - 创建直播拉流任务
        - 更新直播拉流任务
    - 直播流管理
        - 查询流状态
        - 查询直播中的流
    - 流管理
        - 断开直播流
        - 恢复直播流
        - 禁播直播流
        - 查询推断流事件
        - 设置延时直播
        - 取消直播延时
    - 转码模版
        - 创建转码模版
        - 删除转码模版
        - 创建转码规则
        - 删除转码规则

## 使用场景

### MCP 如何赋能 AI Agent

- MCP 提供统一的 protocol + params 语义化接口。
- 签名、证书管理、API版本兼容等问题由 MCP Server 处理，AI Agent 只需关注业务逻辑。
- 标准化错误处理
- 降低开发门槛

### MCP AI Agent 增强场景

- AI驱动的云直播域名自动化运维：
  - 通过MCP协议将腾讯云直播域名管理的操作转化为可调用的工具。
  - 使大模型可根据自然语言指令完成域名管理操作。
- AI运营专员零代码创建拉转推任务：
  - 无需记忆API参数规则，口语化指令直接拉起目标任务。
  - 一键跨平台分发，将直播流一键转发多平台。
- AI直播房间智能化管理：
  - 快速熔断违规直播间，言出即停。
  - 实时掌控活跃直播间信息，联动多平台，纵览全局。
- AI模板管理：
  - 目前已支持转码类模板的智能管理，可通过文本指令进行转码模板的增删改查操作。
