# -*- coding: utf-8 -*-
"""
餐厅管理相关表单定义模块
所有验证消息均为中文
"""

import flask_wtf
import flask_wtf.file
import wtforms
import wtforms.validators
import decimal

from app.models import Restaurant


class RestaurantCreateForm(flask_wtf.FlaskForm):
    """
    餐厅创建表单
    包含餐厅名称和Logo上传
    """
    
    # 餐厅名称字段
    name = wtforms.StringField(
        '餐厅名称',
        validators=[
            wtforms.validators.DataRequired(message='请输入餐厅名称'),
            wtforms.validators.Length(min=1, max=100, message='餐厅名称长度必须在1-100个字符之间')
        ],
        render_kw={'placeholder': '请输入餐厅名称'}
    )
    
    # Logo上传字段 - 修改：移除FileAllowed验证器，支持中文文件名
    logo = flask_wtf.file.FileField(
        '餐厅Logo',
        validators=[
            flask_wtf.file.FileRequired(message='请上传餐厅Logo')
            # 移除FileAllowed验证器，在后端统一处理文件类型验证
        ]
    )
    
    # 提交按钮
    submit = wtforms.SubmitField('创建餐厅')
    
    def validate_name(self, field):
        """
        自定义验证：检查餐厅名称是否已存在
        
        参数:
            field: 餐厅名称字段
        """
        existing = Restaurant.query.filter_by(name=field.data).first()
        if existing:
            raise wtforms.validators.ValidationError('该餐厅名称已被使用，请更换其他名称')
    
    def validate_logo(self, field):
        """
        自定义验证：检查Logo文件，支持中文文件名
        
        参数:
            field: Logo文件字段
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


class DishCreateForm(flask_wtf.FlaskForm):
    """
    菜品创建表单
    包含菜品名称、价格、描述和图片上传
    """
    
    # 菜品名称字段
    name = wtforms.StringField(
        '菜品名称',
        validators=[
            wtforms.validators.DataRequired(message='请输入菜品名称'),
            wtforms.validators.Length(min=1, max=100, message='菜品名称长度必须在1-100个字符之间')
        ],
        render_kw={'placeholder': '请输入菜品名称'}
    )
    
    # 价格字段
    price = wtforms.DecimalField(
        '价格',
        validators=[
            wtforms.validators.DataRequired(message='请输入价格'),
            wtforms.validators.NumberRange(min=0.01, message='价格必须大于0')
        ],
        places=2,
        render_kw={'placeholder': '请输入价格', 'step': '0.01', 'min': '0.01'}
    )
    
    # 描述字段
    description = wtforms.TextAreaField(
        '描述',
        validators=[
            wtforms.validators.DataRequired(message='请输入菜品描述'),
            wtforms.validators.Length(max=500, message='描述不能超过500个字符')
        ],
        render_kw={'placeholder': '请输入菜品描述（最多500字）', 'rows': 4, 'maxlength': 500}
    )
    
    # 图片上传字段 - 修改：移除FileAllowed验证器，支持中文文件名
    image = flask_wtf.file.FileField(
        '菜品图片',
        validators=[
            flask_wtf.file.FileRequired(message='请上传菜品图片')
            # 移除FileAllowed验证器，在后端统一处理文件类型验证
        ]
    )
    
    # 提交按钮
    submit = wtforms.SubmitField('添加菜品')
    
    def validate_image(self, field):
        """
        自定义验证：检查菜品图片文件，支持中文文件名
        
        参数:
            field: 图片文件字段
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