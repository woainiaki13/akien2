# -*- coding: utf-8 -*-
"""
菜品名称匹配模块

使用difflib和SQLAlchemy ilike实现模糊匹配，支持用户使用不精确的菜品名称进行查询。
"""

import difflib
import re
from typing import Optional, List, Tuple

import app.extensions as extensions
db = extensions.db
from app.models import Dish


def extract_dish_name_from_question(question: str) -> Optional[str]:
    """
    从问题中提取可能的菜品名称
    
    使用正则表达式匹配常见的菜品询问模式：
    - "XX怎么样"
    - "XX好吃吗"
    - "有XX吗"
    - "XX多少钱"
    - 引号中的内容
    
    Args:
        question: 用户问题
        
    Returns:
        提取的菜品名称，如果没有匹配则返回None
    """
    patterns = [
        r'[「『"\'](.*?)[」』"\']',  # 引号中的内容
        r'(.{2,10}?)(?:怎么样|好吃吗|好不好|推荐吗)',  # XX怎么样
        r'(?:有|想要|来份|点个|要个)(.{2,10}?)(?:吗|呢|嘛)?$',  # 有XX吗
        r'(.{2,10}?)(?:多少钱|什么价|价格)',  # XX多少钱
        r'(.{2,10}?)(?:卖得|销量|谁点)',  # XX销量
        r'(?:关于|说说|介绍)(.{2,10})',  # 关于XX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            name = match.group(1).strip()
            # 过滤过短或包含常见无关词的结果
            if len(name) >= 2 and not any(w in name for w in ['这个', '那个', '什么', '怎么', '哪个']):
                return name
    
    return None


def fuzzy_match_dish_name(query_name: str, restaurant_id: int, threshold: float = 0.6) -> Optional[Tuple[int, str, float]]:
    """
    使用模糊匹配在餐厅菜品中查找最接近的菜品
    
    Args:
        query_name: 用户输入的菜品名称
        restaurant_id: 餐厅ID
        threshold: 最低匹配度阈值（0-1）
        
    Returns:
        匹配结果元组 (dish_id, dish_name, similarity_score) 或 None
    """
    # 先尝试精确匹配（ilike，不区分大小写）
    exact_match = Dish.query.filter(
        Dish.restaurant_id == restaurant_id,
        Dish.is_available == True,
        Dish.name.ilike(f'%{query_name}%')
    ).first()
    
    if exact_match:
        return (exact_match.id, exact_match.name, 1.0)
    
    # 获取餐厅所有可用菜品
    dishes = Dish.query.filter(
        Dish.restaurant_id == restaurant_id,
        Dish.is_available == True
    ).all()
    
    if not dishes:
        return None
    
    # 使用difflib进行模糊匹配
    dish_names = [d.name for d in dishes]
    matches = difflib.get_close_matches(query_name, dish_names, n=1, cutoff=threshold)
    
    if matches:
        matched_name = matches[0]
        # 计算相似度分数
        similarity = difflib.SequenceMatcher(None, query_name, matched_name).ratio()
        # 找到对应的dish
        for d in dishes:
            if d.name == matched_name:
                return (d.id, d.name, similarity)
    
    return None


def find_dish_by_keywords(keywords: List[str], restaurant_id: int) -> Optional[Tuple[int, str]]:
    """
    使用关键词列表查找菜品
    
    Args:
        keywords: 关键词列表
        restaurant_id: 餐厅ID
        
    Returns:
        匹配结果元组 (dish_id, dish_name) 或 None
    """
    for keyword in keywords:
        if len(keyword) < 2:
            continue
        dish = Dish.query.filter(
            Dish.restaurant_id == restaurant_id,
            Dish.is_available == True,
            Dish.name.ilike(f'%{keyword}%')
        ).first()
        if dish:
            return (dish.id, dish.name)
    
    return None


def is_asking_about_other_dish(question: str, current_dish_name: str) -> bool:
    """
    判断用户是否在询问其他菜品（而非当前菜品）
    
    Args:
        question: 用户问题
        current_dish_name: 当前正在查看的菜品名称
        
    Returns:
        True 如果用户在询问其他菜品
    """
    # 如果问题中提到了当前菜品名称，则不是在问其他菜品
    if current_dish_name.lower() in question.lower():
        return False
    
    # 检查是否有明确询问其他菜品的模式
    other_dish_patterns = [
        r'还有什么|其他.*菜|别的.*菜|推荐.*其他',
        r'[「『"\'](.*?)[」』"\']',  # 引号中可能是其他菜品
        r'(?:有没有|想要|来份|点个)(.{2,10})',
    ]
    
    for pattern in other_dish_patterns:
        if re.search(pattern, question):
            return True
    
    return False


def get_all_dish_names(restaurant_id: int) -> List[str]:
    """
    获取餐厅所有可用菜品的名称列表
    
    Args:
        restaurant_id: 餐厅ID
        
    Returns:
        菜品名称列表
    """
    dishes = Dish.query.filter(
        Dish.restaurant_id == restaurant_id,
        Dish.is_available == True
    ).all()
    return [d.name for d in dishes]
