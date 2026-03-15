# -*- coding: utf-8 -*-
"""\
Flask 应用工厂模块
创建并配置 Flask 应用实例
"""

import os

import flask

import app.config as config
import app.extensions as extensions
import app.models as models


def create_app(config_name=None):
    """\
    应用工厂函数：创建并配置 Flask 应用实例。

    参数:
        config_name: 配置名称（development/production/testing），默认从环境变量 FLASK_ENV 获取

    返回:
        flask.Flask: 配置好的 Flask 应用实例
    """
    app = flask.Flask(__name__)

    # 确定配置类型
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # 加载配置
    config_class = config.config_dict.get(config_name, config.config_dict['default'])
    app.config.from_object(config_class)

    # 初始化扩展
    _init_extensions(app)

    # 注册蓝图
    _register_blueprints(app)

    # 请求前检查：确保用户已完成 DeepSeek API Key 设置流程
    _setup_deepseek_key_gate(app)

    # 创建必要的目录
    _ensure_directories(app)

    # 配置用户加载回调
    _setup_login_manager(app)

    return app


def _init_extensions(app):
    """初始化 Flask 扩展。"""
    # 初始化数据库
    extensions.db.init_app(app)

    # 初始化数据库迁移
    extensions.migrate.init_app(app, extensions.db)

    # 初始化登录管理器
    extensions.login_manager.init_app(app)

    # 初始化 CSRF 保护
    extensions.csrf.init_app(app)

    # 登录跳转端点
    extensions.login_manager.login_view = 'auth.login'


def _register_blueprints(app):
    """注册应用蓝图。"""
    import app.auth as auth
    import app.main as main
    import app.manager as manager
    import app.order as order

    # 导入 AI Blueprint
    from app.ai import ai_bp

    # 注册 AI Blueprint
    app.register_blueprint(ai_bp)

    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(main.main_bp)
    app.register_blueprint(manager.manager_bp)
    app.register_blueprint(order.order_bp)


def _setup_deepseek_key_gate(app):
    """\
    注册 before_request 钩子：确保用户已完成 DeepSeek API Key 初始化流程。

    说明：
    - 若用户未设置 Key 且未选择“跳过使用默认 Key”，则强制跳转到 /ai/key。
    - 对 /ai/key 自身、静态资源等路径豁免，避免重定向循环。
    """

    @app.before_request
    def check_deepseek_key_initialized():
        """\
        请求前检查：确保用户已完成 DeepSeek API Key 设置流程。

        如果用户未设置且不是访问豁免路径，则重定向到 /ai/key
        """
        from app.ai import key_store

        # 豁免路径列表（不需要检查 Key 的路径）
        exempt_prefixes = (
            "/ai/key",      # Key 设置页面本身（含 /ai/key/clear 等）
            "/static",      # 静态文件
            "/favicon",     # 网站图标
        )

        # 检查是否是豁免路径
        request_path = flask.request.path or ""
        if request_path.startswith(exempt_prefixes):
            return None

        # 检查是否已完成 Key 初始化
        # 约定：key_store.is_key_session_initialized() 用于判断是否已“输入或选择跳过”
        if not key_store.is_key_session_initialized():
            # 保存当前请求的 URL，完成后跳回
            next_url = flask.request.url
            return flask.redirect(flask.url_for("ai.key_page", next=next_url))

        return None


def _ensure_directories(app):
    """确保必要的目录存在。"""
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)

    avatar_folder = app.config.get('AVATAR_UPLOAD_FOLDER')
    if avatar_folder:
        os.makedirs(avatar_folder, exist_ok=True)

    logo_folder = app.config.get('LOGO_UPLOAD_FOLDER')
    if logo_folder:
        os.makedirs(logo_folder, exist_ok=True)

    dish_folder = app.config.get('DISH_UPLOAD_FOLDER')
    if dish_folder:
        os.makedirs(dish_folder, exist_ok=True)


def _setup_login_manager(app):
    """配置 Flask-Login 的用户加载回调。"""

    @extensions.login_manager.user_loader
    def load_user(user_id):
        """\
        根据用户 ID 加载用户对象。

        参数:
            user_id: 用户 ID 字符串

        返回:
            models.User|None: 用户对象（不存在则返回 None）
        """
        return models.User.query.get(int(user_id))
