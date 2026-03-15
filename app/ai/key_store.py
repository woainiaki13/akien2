# -*- coding: utf-8 -*-
"""
DeepSeek API Key 存储模块

管理 API Key 的获取优先级：
1. Session 中 TA 手动输入的 Key（最高优先级）
2. 环境变量 DEEPSEEK_API_KEY
3. 程序预设的默认 Key（最低优先级）

设计原则：
- 不在日志或页面中暴露完整 Key
- 使用 Flask session 隔离不同用户
- 支持清除和重置
"""

import os
import flask

# 程序预设的默认 API Key（TA 不输入时使用）
# 注意：实际部署时请替换为有效的 Key
DEFAULT_DEEPSEEK_API_KEY = "sk-7b439e7d82364da389e747303b725cfc"

# Session 中存储 Key 的键名
SESSION_KEY_NAME = "deepseek_api_key"
SESSION_USE_DEFAULT_FLAG = "deepseek_use_default"


def get_deepseek_api_key() -> str:
    """
    获取当前应使用的 DeepSeek API Key

    优先级：
    1. Session 中手动设置的 Key
    2. 环境变量 DEEPSEEK_API_KEY
    3. 程序默认 Key

    Returns:
        API Key 字符串
    """
    # 优先级 1: Session 中的手动输入 Key
    if SESSION_KEY_NAME in flask.session:
        session_key = flask.session.get(SESSION_KEY_NAME, "")
        if session_key:
            return session_key

    # 优先级 2: 环境变量
    env_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if env_key:
        return env_key

    # 优先级 3: 默认 Key
    return DEFAULT_DEEPSEEK_API_KEY


def is_api_key_configured() -> bool:
    """
    检查是否有可用的 API Key

    Returns:
        True 如果有任何来源的 Key 可用
    """
    return bool(get_deepseek_api_key())


def is_key_session_initialized() -> bool:
    """
    检查用户是否已经完成 Key 设置流程

    用户需要至少访问过 /ai/key 页面并做出选择（输入 Key 或选择使用默认）

    Returns:
        True 如果用户已完成初始化
    """
    # 如果 session 中有 Key，说明用户手动输入过
    if flask.session.get(SESSION_KEY_NAME):
        return True
    # 如果有"使用默认"标记，说明用户选择了跳过
    if flask.session.get(SESSION_USE_DEFAULT_FLAG):
        return True
    return False


def set_deepseek_api_key(key: str) -> None:
    """
    在 Session 中设置 API Key

    Args:
        key: 用户输入的 API Key
    """
    flask.session[SESSION_KEY_NAME] = key.strip()
    # 清除"使用默认"标记，因为现在有手动输入的 Key
    flask.session.pop(SESSION_USE_DEFAULT_FLAG, None)
    flask.session.modified = True


def mark_use_default_key() -> None:
    """
    标记用户选择使用默认 Key（跳过手动输入）
    """
    flask.session[SESSION_USE_DEFAULT_FLAG] = True
    flask.session.pop(SESSION_KEY_NAME, None)
    flask.session.modified = True


def clear_api_key() -> None:
    """
    清除 Session 中的 Key 设置，强制用户重新选择
    """
    flask.session.pop(SESSION_KEY_NAME, None)
    flask.session.pop(SESSION_USE_DEFAULT_FLAG, None)
    flask.session.modified = True


def get_key_source() -> str:
    """
    获取当前 Key 的来源描述（中文）

    Returns:
        来源描述字符串
    """
    if flask.session.get(SESSION_KEY_NAME):
        return "手动输入"

    env_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if env_key:
        return "环境变量"

    return "程序默认"


def get_masked_key() -> str:
    """
    获取脱敏后的 Key（仅显示最后 4 位）

    Returns:
        格式如 "****abcd" 的脱敏字符串
    """
    key = get_deepseek_api_key()
    if not key:
        return "（未设置）"
    if len(key) <= 4:
        return "****"
    return "****" + key[-4:]
