# -*- coding: utf-8 -*-
"""
认证蓝图模块
处理用户注册、登录、登出等功能
"""

import flask

# 创建认证蓝图
auth_bp = flask.Blueprint('auth', __name__, url_prefix='/auth')

# 导入路由（必须在蓝图创建后导入，避免循环导入）
from app.auth import routes
