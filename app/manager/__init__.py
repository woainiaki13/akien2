# -*- coding: utf-8 -*-
"""
餐厅管理蓝图模块
处理餐厅创建、菜品管理等功能
"""

import flask

# 创建餐厅管理蓝图，URL前缀为/manager
manager_bp = flask.Blueprint('manager', __name__, url_prefix='/manager')

# 导入路由模块（必须在蓝图创建后导入，避免循环导入）
from app.manager import routes
