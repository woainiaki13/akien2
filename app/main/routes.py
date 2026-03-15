# -*- coding: utf-8 -*-
"""
主页面路由模块
处理首页、选择页面和功能入口页面
"""

import flask
import flask_login

from app.main import main_bp


@main_bp.route('/')
def index():
    """
    首页视图
    已登录用户重定向到选择页面
    未登录用户显示欢迎页面和登录/注册链接
    """
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('main.choice'))
    return flask.render_template('main/index.html')


@main_bp.route('/choice')
@flask_login.login_required
def choice():
    """
    选择页面视图（需要登录）
    显示用户头像和两个功能选项：管理餐厅 / 订餐
    """
    return flask.render_template('main/choice.html')


@main_bp.route('/manage')
@flask_login.login_required
def manage_placeholder():
    """
    管理餐厅入口（重定向到manager蓝图）
    保持与Step-1的兼容性
    """
    return flask.redirect(flask.url_for('manager.home'))


@main_bp.route('/order')
@flask_login.login_required
def order_placeholder():
    """
    订餐入口（重定向到order蓝图）
    保持与Step-1/2的兼容性
    """
    return flask.redirect(flask.url_for('order.home'))
