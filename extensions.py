# -*- coding: utf-8 -*-
"""
应用常量定义模块
包含类别映射、UI文本等常量
所有用户界面文本均为中文
"""

# 固定分类内部值（英文）列表
FIXED_CATEGORIES = ["Drink", "Dish", "Staple", "Other"]

# 类别中文显示名称映射
CATEGORY_LABELS = {
    'Drink': '饮品',
    'Dish': '菜品',
    'Staple': '主食',
    'Other': '其他'
}

# 订单状态映射
ORDER_STATUS = {
    'DRAFT': '草稿',
    'PAID': '已支付',
    'COMPLETED': '已完成',
    'CANCELLED': '已取消'
}

# UI文本常量（中文）
UI_TEXT = {
    "app_name": "网络餐厅平台",
    # 通用文本
    'common': {
        'back': '返回',
        'submit': '提交',
        'delete': '删除',
        'edit': '编辑',
        'save': '保存',
        'cancel': '取消',
        'confirm': '确认',
        'success': '成功',
        'error': '错误',
        'warning': '警告',
        'loading': '加载中...',
        'no_data': '暂无数据',
        'operation_success': '操作成功',
        'operation_failed': '操作失败',
        'price_unit': '元',
    },
    
    # 餐厅相关文本
    'restaurant': {
        'title': '餐厅管理',
        'create_title': '创建餐厅',
        'create_btn': '创建餐厅',
        'name_label': '餐厅名称',
        'name_placeholder': '请输入餐厅名称',
        'logo_label': '餐厅Logo',
        'logo_help': '支持 jpg、jpeg、png、webp 格式图片',
        'create_success': '餐厅创建成功！',
        'create_failed': '餐厅创建失败，请稍后重试。',
        'name_exists': '该餐厅名称已被使用，请更换其他名称。',
        'name_required': '请输入餐厅名称',
        'name_too_long': '餐厅名称不能超过100个字符',
        'logo_required': '请上传餐厅Logo',
        'no_restaurant': '您还没有创建餐厅',
        'no_restaurant_hint': '请先创建一个餐厅以开始管理菜品',
        'dashboard_title': '餐厅仪表盘',
    },
    
    # 菜品相关文本
    'dish': {
        'title': '菜品管理',
        'add_title': '添加菜品',
        'add_btn': '添加菜品',
        'name_label': '菜品名称',
        'name_placeholder': '请输入菜品名称',
        'name_required': '请输入菜品名称',
        'name_too_long': '菜品名称不能超过100个字符',
        'price_label': '价格',
        'price_placeholder': '请输入价格',
        'price_required': '请输入价格',
        'price_invalid': '请输入有效的价格',
        'price_positive': '价格必须大于0',
        'description_label': '描述',
        'description_placeholder': '请输入菜品描述（最多500字）',
        'description_required': '请输入菜品描述',
        'description_too_long': '描述不能超过500个字符',
        'image_label': '菜品图片',
        'image_help': '支持 jpg、jpeg、png、webp 格式，图片将自动调整至100×100像素以内',
        'image_required': '请上传菜品图片',
        'add_success': '菜品添加成功！',
        'add_failed': '菜品添加失败，请稍后重试。',
        'delete_success': '菜品删除成功！',
        'delete_failed': '菜品删除失败，请稍后重试。',
        'delete_confirm': '确定要删除这个菜品吗？删除后无法恢复。',
        'no_dishes': '该分类下暂无菜品',
        'no_permission': '您没有权限执行此操作',
    },
    
    # 分类相关文本
    'category': {
        'title': '菜品分类',
        'select': '选择分类',
    },
    
    # 图片上传相关文本
    'image': {
        'invalid_format': '不支持的图片格式，请上传 jpg、jpeg、png 或 webp 格式的图片',
        'invalid_file': '无法打开图片文件，请确保上传的是有效的图片',
        'upload_failed': '图片上传失败，请稍后重试',
    },
    
    # 导航相关文本
    'nav': {
        'home': '首页',
        'manage_restaurant': '管理餐厅',
        'order_food': '订餐',
        'logout': '退出登录',
        'back_to_choice': '返回选择页面',
    },
}
