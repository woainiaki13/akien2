# -*- coding: utf-8 -*-
"""\
Flask 扩展实例化模块
所有扩展在此统一创建，避免循环导入

注意：
- 不要在应用工厂阶段访问 db.engine（容易触发 "Working outside of application context"）
- SQLite 外键约束必须显式开启，否则 ondelete='CASCADE' 不生效
"""

import sqlite3

import flask_login
import flask_migrate
import flask_sqlalchemy
import flask_wtf.csrf
import sqlalchemy
import sqlalchemy.engine


# 数据库 ORM 扩展
db = flask_sqlalchemy.SQLAlchemy()

# 数据库迁移扩展
migrate = flask_migrate.Migrate()

# 用户登录管理扩展
login_manager = flask_login.LoginManager()
# 设置登录视图的端点
login_manager.login_view = 'auth.login'
# 设置登录提示消息
login_manager.login_message = '请先登录后再访问此页面。'
login_manager.login_message_category = 'warning'

# CSRF 保护扩展
csrf = flask_wtf.csrf.CSRFProtect()


@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, 'connect')
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """\
    为 SQLite 连接启用外键约束。

    说明：
    - 只对 sqlite3.Connection 生效，避免对其他数据库执行 PRAGMA 造成报错。
    - 该监听器挂在 sqlalchemy.engine.Engine 上，不依赖 Flask app context。
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()
