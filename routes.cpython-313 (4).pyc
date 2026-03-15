# -*- coding: utf-8 -*-
"""
认证相关表单定义模块
"""

import flask_wtf
import flask_wtf.file
import wtforms
import wtforms.validators

from app.models import User


class RegisterForm(flask_wtf.FlaskForm):
    """用户注册表单"""
    
    # 用户名字段
    username = wtforms.StringField(
        '用户名',
        validators=[
            wtforms.validators.DataRequired(message='用户名不能为空'),
            wtforms.validators.Length(min=2, max=64, message='用户名长度必须在2-64个字符之间')
        ]
    )
    
    # 邮箱字段
    email = wtforms.StringField(
        '邮箱',
        validators=[
            wtforms.validators.DataRequired(message='邮箱不能为空'),
            wtforms.validators.Email(message='请输入有效的邮箱地址'),
            wtforms.validators.Length(max=120, message='邮箱长度不能超过120个字符')
        ]
    )
    
    # 密码字段
    password = wtforms.PasswordField(
        '密码',
        validators=[
            wtforms.validators.DataRequired(message='密码不能为空'),
            wtforms.validators.Length(min=6, max=128, message='密码长度必须在6-128个字符之间')
        ]
    )
    
    # 确认密码字段
    confirm_password = wtforms.PasswordField(
        '确认密码',
        validators=[
            wtforms.validators.DataRequired(message='请确认密码'),
            wtforms.validators.EqualTo('password', message='两次输入的密码不一致')
        ]
    )
    
    # 头像上传字段 - 修改：移除FileAllowed验证器，支持中文文件名
    avatar = flask_wtf.file.FileField(
        '头像',
        validators=[
            flask_wtf.file.FileRequired(message='请上传头像图片')
            # 移除FileAllowed验证器，在后端统一处理文件类型验证
        ]
    )
    
    # 提交按钮
    submit = wtforms.SubmitField('注册')
    
    def validate_username(self, field):
        """
        自定义验证：检查用户名是否已存在
        
        参数:
            field: 用户名字段
        """
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise wtforms.validators.ValidationError('该用户名已被注册，请选择其他用户名。')
    
    def validate_email(self, field):
        """
        自定义验证：检查邮箱是否已存在
        
        参数:
            field: 邮箱字段
        """
        user = User.query.filter_by(email=field.data.lower()).first()
        if user:
            raise wtforms.validators.ValidationError('该邮箱已被注册，请使用其他邮箱。')
    
    def validate_avatar(self, field):
        """
        自定义验证：检查头像文件，支持中文文件名
        
        参数:
            field: 头像文件字段
        """
        if field.data:
            filename = field.data.filename
            
            # 检查文件扩展名（支持中文文件名）
            if '.' not in filename:
                raise wtforms.validators.ValidationError('文件缺少扩展名')
            
            # 获取扩展名并转换为小写
            extension = filename.rsplit('.', 1)[1].lower()
            allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
            
            if extension not in allowed_extensions:
                raise wtforms.validators.ValidationError('不支持的图片格式，请上传 jpg、jpeg、png 或 webp 格式的图片')


class LoginForm(flask_wtf.FlaskForm):
    """用户登录表单"""
    
    # 邮箱字段
    email = wtforms.StringField(
        '邮箱',
        validators=[
            wtforms.validators.DataRequired(message='请输入邮箱'),
            wtforms.validators.Email(message='请输入有效的邮箱地址')
        ]
    )
    
    # 密码字段
    password = wtforms.PasswordField(
        '密码',
        validators=[
            wtforms.validators.DataRequired(message='请输入密码')
        ]
    )
    
    # 记住我复选框
    remember_me = wtforms.BooleanField('记住我')
    
    # 提交按钮
    submit = wtforms.SubmitField('登录')