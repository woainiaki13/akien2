# -*- coding: utf-8 -*-
"""
AI 模块路由

提供 API Key 管理相关的路由：
- GET/POST /ai/key - 输入或查看 Key
- POST /ai/key/clear - 清除 Key
"""

import flask
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.ai import key_store

# 创建 Blueprint
ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


@ai_bp.route("/key", methods=["GET", "POST"])
def key_page():
    """
    API Key 输入页面

    GET: 显示输入表单和当前状态
    POST: 保存 Key 或标记使用默认
    """
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "save":
            # 保存用户输入的 Key
            user_key = request.form.get("api_key", "").strip()
            if user_key:
                key_store.set_deepseek_api_key(user_key)
                flash("API Key 已保存", "success")
            else:
                # 如果提交了空 Key，视为使用默认
                key_store.mark_use_default_key()
                flash("未输入 Key，将使用程序默认 Key", "info")

        elif action == "skip":
            # 跳过，使用默认 Key
            key_store.mark_use_default_key()
            flash("已选择使用默认 Key", "info")

        elif action == "clear":
            # 清除 Key
            key_store.clear_api_key()
            flash("已清除 Key 设置，请重新输入", "info")
            return redirect(url_for("ai.key_page"))

        # 获取来源页面，如果没有则跳转到首页
        next_url = request.form.get("next") or request.args.get("next") or "/"
        # 防止重定向到 key 页面本身造成循环
        if "/ai/key" in next_url:
            next_url = "/"
        return redirect(next_url)

    # GET 请求：显示页面
    return render_template(
        "ai/key.html",
        is_initialized=key_store.is_key_session_initialized(),
        key_source=key_store.get_key_source(),
        masked_key=key_store.get_masked_key(),
        next_url=request.args.get("next", "/")
    )


@ai_bp.route("/key/clear", methods=["POST"])
def clear_key():
    """
    清除 API Key 设置
    """
    key_store.clear_api_key()
    flash("已清除 Key 设置", "info")
    return redirect(url_for("ai.key_page"))
