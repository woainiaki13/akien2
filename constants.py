# -*- coding: utf-8 -*-
"""
应用配置模块
包含不同环境的配置类
"""

import os


class Config:
    """基础配置类"""
    
    # 安全密钥，用于session和CSRF保护
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-secret-key'
    
    # 数据库配置
    # 默认使用SQLite，可通过DATABASE_URL环境变量切换
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or \
        os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    
    # 头像上传子目录
    AVATAR_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
    
    # Logo上传子目录
    LOGO_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'logos')
    
    # 菜品图片上传子目录
    DISH_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'dishes')
    
    # 最大上传文件大小：2MB
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    
    # 允许的图片文件扩展名
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    
    # 头像最大尺寸（像素）
    AVATAR_MAX_SIZE = (100, 100)
    
    # Logo最大尺寸（像素）
    LOGO_MAX_SIZE = (200, 200)
    
    # 菜品图片最大尺寸（像素）
    DISH_IMAGE_MAX_SIZE = (100, 100)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置映射字典
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
