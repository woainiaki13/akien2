# -*- coding: utf-8 -*-
"""
认证相关路由模块
处理用户注册、登录、登出的请求
"""

import flask
import flask_login

from app.auth import auth_bp
from app.auth.forms import RegisterForm, LoginForm
from app.extensions import db
from app.models import User
from app.utils.images import save_avatar


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册视图
    GET: 显示注册表单
    POST: 处理注册请求
    """
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('main.choice'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            # 后端文件大小验证
            if form.avatar.data:
                # 检查文件大小（2MB限制）
                if form.avatar.data.content_length > 2 * 1024 * 1024:
                    flask.flash('头像文件大小不能超过2MB', 'danger')
                    return flask.render_template('auth/register.html', form=form)
            
            # 获取头像上传目录
            upload_dir = flask.current_app.config['AVATAR_UPLOAD_FOLDER']
            max_size = flask.current_app.config['AVATAR_MAX_SIZE']
            
            # 保存头像并获取相对路径
            avatar_path = save_avatar(form.avatar.data, upload_dir, max_size)
            
            # 确保头像路径使用Web兼容的正斜杠
            if avatar_path:
                avatar_path = avatar_path.replace('\\', '/')
            
            # 创建新用户
            user = User(
                username=form.username.data,
                email=form.email.data.lower(),
                avatar_path=avatar_path
            )
            user.set_password(form.password.data)
            
            # 保存到数据库
            db.session.add(user)
            db.session.commit()
            
            # 自动登录新注册用户
            flask_login.login_user(user)
            
            flask.flash('注册成功！欢迎加入。', 'success')
            return flask.redirect(flask.url_for('main.choice'))
            
        except ValueError as e:
            # 头像处理错误（如格式不支持）
            flask.flash(str(e), 'danger')
        except Exception as e:
            # 其他错误，回滚数据库事务
            db.session.rollback()
            flask.flash(f'注册失败，请稍后重试。错误: {str(e)}', 'danger')
    
    return flask.render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录视图
    GET: 显示登录表单
    POST: 处理登录请求
    """
    # 如果用户已登录，重定向到选择页面
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('main.choice'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # 根据邮箱查找用户
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user is None or not user.check_password(form.password.data):
            flask.flash('邮箱或密码错误，请重试。', 'danger')
            return flask.redirect(flask.url_for('auth.login'))
        
        # 登录用户
        flask_login.login_user(user, remember=form.remember_me.data)
        
        flask.flash('登录成功！', 'success')
        
        # 检查是否有 next 参数，用于重定向到原本要访问的页面
        next_page = flask.request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = flask.url_for('main.choice')
        
        return flask.redirect(next_page)
    
    return flask.render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@flask_login.login_required
def logout():
    """
    用户登出视图
    登出当前用户并重定向到首页
    """
    flask_login.logout_user()
    flask.flash('您已成功登出。', 'info')
    return flask.redirect(flask.url_for('main.index'))