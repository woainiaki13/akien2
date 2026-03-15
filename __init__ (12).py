# -*- coding: utf-8 -*-
"""
主页面蓝图模块
处理首页、选择页面和占位页面
"""

import flask

# 创建主蓝图
main_bp = flask.Blueprint('main', __name__)

# 导入路由（必须在蓝图创建后导入，避免循环导入）
from app.main import routes
