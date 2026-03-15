# -*- coding: utf-8 -*-
"""
DeepSeek API 客户端模块

封装与 DeepSeek API 的交互，提供统一的接口。

修改说明：
- 改用 key_store 模块获取 API Key，支持多来源优先级
- 保持原有 base_url/model/timeout 的环境变量配置
"""

import os
import requests
from typing import List, Dict, Optional

from app.ai import key_store

# API 配置（从环境变量读取，有默认值）
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT_SECONDS = int(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "30"))


def is_api_configured() -> bool:
    """
    检查 DeepSeek API 是否已配置（有可用的 Key）

    使用 key_store 检查，支持三级来源：Session > 环境变量 > 默认 Key

    Returns:
        True 如果有可用的 API Key
    """
    return key_store.is_api_key_configured()


def call_chat_completion(
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 1000,
        model_override: Optional[str] = None
) -> str:
    """
    调用 DeepSeek Chat Completion API

    Args:
        messages: 消息列表，格式为 [{"role": "system/user/assistant", "content": "..."}]
        temperature: 温度参数，控制随机性（0-2）
        max_tokens: 最大生成 token 数
        model_override: 可选的模型覆盖

    Returns:
        助手回复的文本内容

    Raises:
        ValueError: API Key 未设置
        TimeoutError: 请求超时
        ConnectionError: 网络连接失败
        RuntimeError: API 返回错误
    """
    # 获取 API Key（从 key_store，支持多来源）
    api_key = key_store.get_deepseek_api_key()

    if not api_key:
        raise ValueError("DeepSeek API Key 未设置")

    # 确定使用的模型
    model = model_override or DEEPSEEK_MODEL

    # 构建请求
    url = f"{DEEPSEEK_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=DEEPSEEK_TIMEOUT_SECONDS
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(f"API 请求超时（{DEEPSEEK_TIMEOUT_SECONDS}秒）")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("无法连接到 API 服务器，请检查网络")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"请求失败: {str(e)}")

    # 解析响应
    if response.status_code != 200:
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
        except Exception:
            error_msg = response.text
        raise RuntimeError(f"API 错误 ({response.status_code}): {error_msg}")

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"解析响应失败: {str(e)}")


def get_error_message(exception: Exception) -> str:
    """
    将异常转换为用户友好的中文错误消息

    Args:
        exception: 捕获的异常

    Returns:
        中文错误消息
    """
    if isinstance(exception, ValueError):
        return "智能问答功能未配置，请联系管理员设置 API Key。"
    elif isinstance(exception, TimeoutError):
        return "请求超时，请稍后再试。"
    elif isinstance(exception, ConnectionError):
        return "网络连接失败，请检查网络后重试。"
    elif isinstance(exception, RuntimeError):
        error_str = str(exception)
        if "401" in error_str or "Unauthorized" in error_str:
            return "API Key 无效或已过期，请检查 Key 是否正确。"
        elif "429" in error_str:
            return "请求过于频繁，请稍后再试。"
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            return "API 服务暂时不可用，请稍后再试。"
        return f"服务出错：{error_str}"
    else:
        return f"未知错误：{str(exception)}"
