# -*- coding: utf-8 -*-
"""
图像处理工具模块
包含头像、Logo、菜品图片的上传、验证和处理函数
"""

import os
import uuid
import re
import PIL.Image
import werkzeug.utils

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}


def convert_chinese_filename_to_english(filename):
    """
    将中文文件名转换为安全的英文文件名
    
    参数:
        filename: 原始文件名（可能包含中文）
        
    返回:
        str: 转换后的英文文件名
    """
    if not filename:
        return f"image_{uuid.uuid4().hex}"
    
    # 分离文件名和扩展名
    name_part, ext_part = os.path.splitext(filename)
    
    # 如果文件名已经是英文，直接返回
    if all(ord(c) < 128 for c in name_part):
        return filename
    
    # 中文文件名转换为英文：移除非字母数字字符，保留基本字符
    safe_name = re.sub(r'[^\w\s-]', '', name_part)  # 移除非字母数字字符
    safe_name = re.sub(r'[-\s]+', '_', safe_name)    # 将空格和连字符转换为下划线
    
    # 如果移除中文后名字为空，使用UUID
    if not safe_name:
        safe_name = f"image_{uuid.uuid4().hex}"
    
    # 确保文件名长度合理
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    return f"{safe_name}{ext_part}"


def allowed_image_file(filename):
    """
    检查文件扩展名是否允许
    
    参数:
        filename: 文件名
        
    返回:
        bool: 是否允许该扩展名
    """
    if '.' not in filename:
        return False
    # 获取扩展名并转换为小写进行比较
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def allowed_avatar_file(filename):
    """
    检查头像文件扩展名是否允许（兼容旧接口）
    
    参数:
        filename: 文件名
        
    返回:
        bool: 是否允许该扩展名
    """
    return allowed_image_file(filename)


def _process_and_save_image(file_storage, upload_dir, max_size, subfolder_name):
    """
    内部函数：处理并保存图片，自动处理中文文件名
    
    参数:
        file_storage: werkzeug.datastructures.FileStorage对象
        upload_dir: 上传目录的绝对路径
        max_size: 最大尺寸元组 (宽, 高)
        subfolder_name: 子文件夹名称（用于构建相对路径）
        
    返回:
        str: 保存成功返回相对路径
        
    异常:
        ValueError: 如果文件不是有效图像或扩展名不允许
    """
    # 获取原始文件名
    original_filename = file_storage.filename
    
    # 检查文件扩展名
    if not allowed_image_file(original_filename):
        raise ValueError('不支持的图片格式，请上传 jpg、jpeg、png 或 webp 格式的图片')
    
    # 强制将文件名转换为英文（避免中文路径问题）
    english_filename = convert_chinese_filename_to_english(original_filename)
    
    # 获取文件扩展名
    extension = english_filename.rsplit('.', 1)[1].lower()
    
    # 生成唯一文件名，使用UUID避免文件名冲突
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # 确保上传目录存在
    os.makedirs(upload_dir, exist_ok=True)
    
    # 构建完整的保存路径
    save_path = os.path.join(upload_dir, unique_filename)
    
    try:
        # 使用PIL打开图像文件
        image = PIL.Image.open(file_storage)
        
        # 验证是否为有效图像
        image.verify()
        
        # verify()后需要重新打开文件
        file_storage.seek(0)
        image = PIL.Image.open(file_storage)
        
    except Exception as e:
        raise ValueError(f'无法打开图片文件，请确保上传的是有效的图片')
    
    # 检查图像尺寸，如果超过最大尺寸则缩放
    if image.width > max_size[0] or image.height > max_size[1]:
        # 使用thumbnail方法等比例缩放，保持宽高比
        image.thumbnail(max_size, PIL.Image.Resampling.LANCZOS)
    
    # 处理不同图像模式
    # JPEG不支持RGBA模式，需要转换
    if extension in ('jpg', 'jpeg'):
        if image.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = PIL.Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
    
    # 保存图像
    if extension in ('jpg', 'jpeg'):
        image.save(save_path, 'JPEG', quality=85)
    elif extension == 'png':
        image.save(save_path, 'PNG')
    elif extension == 'webp':
        image.save(save_path, 'WEBP', quality=85)
    
    # 返回相对路径，用于存储到数据库和前端显示
    relative_path = os.path.join('uploads', subfolder_name, unique_filename)
    
    # 确保返回的路径使用正斜杠，兼容Web
    return relative_path.replace('\\', '/')


def save_avatar(file_storage, upload_dir, max_size=(100, 100)):
    """
    保存头像文件，自动调整尺寸，处理中文文件名
    
    参数:
        file_storage: werkzeug.datastructures.FileStorage对象
        upload_dir: 上传目录的绝对路径
        max_size: 最大尺寸元组 (宽, 高)，默认 (100, 100)
        
    返回:
        str: 保存成功返回相对路径（如 "uploads/avatars/xxx.jpg"）
        
    异常:
        ValueError: 如果文件不是有效图像或扩展名不允许
    """
    result = _process_and_save_image(file_storage, upload_dir, max_size, 'avatars')
    if result and isinstance(result, str):
        result = result.replace('\\', '/')
    
    return result


def save_logo(file_storage, upload_dir, max_size=(200, 200)):
    """
    保存餐厅Logo文件，自动调整尺寸，处理中文文件名
    
    参数:
        file_storage: werkzeug.datastructures.FileStorage对象
        upload_dir: 上传目录的绝对路径
        max_size: 最大尺寸元组 (宽, 高)，默认 (200, 200)
        
    返回:
        str: 保存成功返回相对路径（如 "uploads/logos/xxx.jpg"）
        
    异常:
        ValueError: 如果文件不是有效图像或扩展名不允许
    """
    result = _process_and_save_image(file_storage, upload_dir, max_size, 'logos')
    if result and isinstance(result, str):
        result = result.replace('\\', '/')
    
    return result


def save_dish_image(file_storage, upload_dir, max_size=(100, 100)):
    """
    保存菜品图片文件，自动调整尺寸到100x100以内，处理中文文件名
    
    参数:
        file_storage: werkzeug.datastructures.FileStorage对象
        upload_dir: 上传目录的绝对路径
        max_size: 最大尺寸元组 (宽, 高)，默认 (100, 100)
        
    返回:
        str: 保存成功返回相对路径（如 "uploads/dishes/xxx.jpg"）
        
    异常:
        ValueError: 如果文件不是有效图像或扩展名不允许
    """
    result = _process_and_save_image(file_storage, upload_dir, max_size, 'dishes')
    if result and isinstance(result, str):
        result = result.replace('\\', '/')
    
    return result