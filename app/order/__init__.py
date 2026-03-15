# -*- coding: utf-8 -*-
"""
订餐蓝图模块
处理顾客浏览餐厅、点餐、购物车、结算等功能
"""

import flask

# 创建订餐蓝图，URL前缀为/order
order_bp = flask.Blueprint('order', __name__, url_prefix='/order')

# 导入路由模块（必须在蓝图创建后导入，避免循环导入）
from app.order import routes
