# -*- coding: utf-8 -*-
"""
QA引擎核心模块

实现规则匹配、数据快照构建、LLM调用的统一接口。
支持经营顾问和菜品问答两种场景。

所有统计数据仅计算 Order.status == "PAID" 的订单。
"""

import json
import re
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy import func, desc

import app.extensions as extensions
db = extensions.db
from app.models import Restaurant, Dish, Order, OrderItem, User
from app.ai import deepseek_client
from app.ai import qa_prompts
from app.ai import qa_matcher


# ============================================================
# 数据快照构建器
# ============================================================

def build_restaurant_snapshot(restaurant_id: int) -> Dict[str, Any]:
    """
    构建餐厅经营数据快照
    
    收集餐厅的核心经营指标，用于经营顾问问答的上下文。
    所有订单统计仅包含 status == 'PAID' 的订单。
    
    Args:
        restaurant_id: 餐厅ID
        
    Returns:
        包含经营数据的字典
    """
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return {"error": "餐厅不存在"}
    
    snapshot = {
        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "description": getattr(restaurant, 'description', ''),
        },
        "snapshot_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "仅统计已支付(PAID)订单"
    }
    
    # 基础统计
    paid_orders = Order.query.filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    )
    
    # 总营收
    total_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).scalar()
    
    snapshot["total_revenue"] = float(total_revenue or 0)
    snapshot["total_orders"] = paid_orders.count()
    
    # 售出菜品总数
    total_dishes_sold = db.session.query(
        func.coalesce(func.sum(OrderItem.quantity), 0)
    ).join(Order, OrderItem.order_id == Order.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).scalar()
    
    snapshot["total_dishes_sold"] = int(total_dishes_sold or 0)
    
    # 顶级消费者排行榜（按总消费金额）
    top_consumers_query = db.session.query(
        User.id,
        User.username,
        User.avatar,
        func.sum(Order.total_amount).label('total_spent'),
        func.count(Order.id).label('order_count')
    ).join(Order, Order.user_id == User.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).group_by(User.id).order_by(desc('total_spent')).limit(10)
    
    snapshot["top_consumers"] = [
        {
            "user_id": row.id,
            "username": row.username,
            "avatar": row.avatar,
            "total_spent": float(row.total_spent or 0),
            "order_count": row.order_count
        }
        for row in top_consumers_query.all()
    ]
    
    # 为每个顶级消费者添加最爱菜品
    for consumer in snapshot["top_consumers"]:
        favorite_dishes = db.session.query(
            Dish.name,
            func.sum(OrderItem.quantity).label('qty')
        ).join(OrderItem, Dish.id == OrderItem.dish_id
        ).join(Order, OrderItem.order_id == Order.id).filter(
            Order.user_id == consumer["user_id"],
            Order.restaurant_id == restaurant_id,
            Order.status == 'PAID'
        ).group_by(Dish.id).order_by(desc('qty')).limit(3).all()
        
        consumer["favorite_dishes"] = [
            {"name": d.name, "quantity": int(d.qty)} for d in favorite_dishes
        ]
    
    # 菜品销量排行榜
    dish_rankings_by_qty = db.session.query(
        Dish.id,
        Dish.name,
        Dish.price,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
    ).join(OrderItem, Dish.id == OrderItem.dish_id
    ).join(Order, OrderItem.order_id == Order.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).group_by(Dish.id).order_by(desc('total_qty')).limit(10).all()
    
    snapshot["dish_rankings_by_qty"] = [
        {
            "dish_id": d.id,
            "name": d.name,
            "price": float(d.price),
            "total_quantity": int(d.total_qty),
            "total_revenue": float(d.total_revenue or 0)
        }
        for d in dish_rankings_by_qty
    ]
    
    # 菜品收入排行榜
    dish_rankings_by_revenue = db.session.query(
        Dish.id,
        Dish.name,
        Dish.price,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
    ).join(OrderItem, Dish.id == OrderItem.dish_id
    ).join(Order, OrderItem.order_id == Order.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).group_by(Dish.id).order_by(desc('total_revenue')).limit(10).all()
    
    snapshot["dish_rankings_by_revenue"] = [
        {
            "dish_id": d.id,
            "name": d.name,
            "price": float(d.price),
            "total_quantity": int(d.total_qty),
            "total_revenue": float(d.total_revenue or 0)
        }
        for d in dish_rankings_by_revenue
    ]
    
    # 最近订单摘要（最近7天）
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_orders = Order.query.filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID',
        Order.created_at >= seven_days_ago
    ).order_by(desc(Order.created_at)).limit(20).all()
    
    snapshot["recent_orders"] = [
        {
            "order_id": o.id,
            "user_id": o.user_id,
            "total_amount": float(o.total_amount),
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""
        }
        for o in recent_orders
    ]
    
    # 餐厅所有菜品列表
    all_dishes = Dish.query.filter(
        Dish.restaurant_id == restaurant_id,
        Dish.is_available == True
    ).all()
    
    snapshot["all_dishes"] = [
        {
            "id": d.id,
            "name": d.name,
            "price": float(d.price),
            "category": getattr(d, 'category', ''),
            "description": d.description[:50] if d.description else ""
        }
        for d in all_dishes
    ]
    
    return snapshot


def build_dish_snapshot(dish_id: int) -> Dict[str, Any]:
    """
    构建菜品数据快照
    
    收集菜品的详细信息和销售数据，用于菜品问答的上下文。
    所有订单统计仅包含 status == 'PAID' 的订单。
    
    Args:
        dish_id: 菜品ID
        
    Returns:
        包含菜品数据的字典
    """
    dish = Dish.query.get(dish_id)
    if not dish:
        return {"error": "菜品不存在"}
    
    restaurant = Restaurant.query.get(dish.restaurant_id)
    
    snapshot = {
        "current_dish": {
            "id": dish.id,
            "name": dish.name,
            "description": dish.description or "",
            "price": float(dish.price),
            "category": getattr(dish, 'category', ''),
            "is_available": dish.is_available,
            "image": getattr(dish, 'image', ''),
        },
        "restaurant": {
            "id": restaurant.id if restaurant else None,
            "name": restaurant.name if restaurant else ""
        },
        "snapshot_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "仅统计已支付(PAID)订单"
    }
    
    # 销售统计
    sales_stats = db.session.query(
        func.coalesce(func.sum(OrderItem.quantity), 0).label('total_qty'),
        func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label('total_revenue'),
        func.count(func.distinct(Order.user_id)).label('unique_buyers')
    ).join(Order, OrderItem.order_id == Order.id).filter(
        OrderItem.dish_id == dish_id,
        Order.status == 'PAID'
    ).first()
    
    snapshot["sales_stats"] = {
        "total_quantity_sold": int(sales_stats.total_qty or 0),
        "total_revenue": float(sales_stats.total_revenue or 0),
        "unique_buyers_count": int(sales_stats.unique_buyers or 0)
    }
    
    # 购买者列表
    buyers_query = db.session.query(
        User.id,
        User.username,
        User.avatar,
        func.sum(OrderItem.quantity).label('qty_purchased')
    ).join(Order, Order.user_id == User.id
    ).join(OrderItem, OrderItem.order_id == Order.id).filter(
        OrderItem.dish_id == dish_id,
        Order.status == 'PAID'
    ).group_by(User.id).order_by(desc('qty_purchased')).limit(20).all()
    
    snapshot["buyers"] = [
        {
            "user_id": b.id,
            "username": b.username,
            "avatar": b.avatar,
            "quantity_purchased": int(b.qty_purchased)
        }
        for b in buyers_query
    ]
    
    # 同类别相关菜品
    if hasattr(dish, 'category') and dish.category:
        related_dishes = Dish.query.filter(
            Dish.restaurant_id == dish.restaurant_id,
            Dish.category == dish.category,
            Dish.id != dish_id,
            Dish.is_available == True
        ).limit(5).all()
    else:
        related_dishes = Dish.query.filter(
            Dish.restaurant_id == dish.restaurant_id,
            Dish.id != dish_id,
            Dish.is_available == True
        ).limit(5).all()
    
    snapshot["related_dishes"] = [
        {
            "id": d.id,
            "name": d.name,
            "price": float(d.price),
            "description": d.description[:30] if d.description else ""
        }
        for d in related_dishes
    ]
    
    # 餐厅所有菜品列表（用于回答"还有什么菜"类问题）
    all_dishes = Dish.query.filter(
        Dish.restaurant_id == dish.restaurant_id,
        Dish.is_available == True
    ).all()
    
    snapshot["restaurant_dishes"] = [
        {
            "id": d.id,
            "name": d.name,
            "price": float(d.price),
            "category": getattr(d, 'category', '')
        }
        for d in all_dishes
    ]
    
    return snapshot


# ============================================================
# 规则引擎
# ============================================================

def try_rule_answer_manager(question: str, restaurant_id: int) -> Optional[str]:
    """
    尝试使用规则匹配回答经营顾问问题
    
    对于常见的分析类问题，直接通过SQL查询返回答案，无需调用LLM。
    
    Args:
        question: 用户问题
        restaurant_id: 餐厅ID
        
    Returns:
        规则匹配的答案，如果没有匹配则返回None
    """
    question_lower = question.lower()
    
    # 模式1: 谁是VIP/谁消费最多/顶级客户
    if re.search(r'(vip|消费.*最多|顶级.*客户|最.*客户|谁.*花.*最多|大客户)', question_lower):
        return _get_top_consumers_answer(restaurant_id)
    
    # 模式2: 哪个菜卖得最好/销量冠军/最受欢迎
    if re.search(r'(卖得.*最好|销量.*最|最.*销量|最受欢迎|畅销|爆款|哪.*菜.*好)', question_lower):
        return _get_top_dishes_answer(restaurant_id)
    
    # 模式3: 总营收/总收入
    if re.search(r'(总营收|总收入|赚了多少|营业额|总.*钱)', question_lower):
        return _get_revenue_answer(restaurant_id)
    
    # 模式4: 订单数/多少订单
    if re.search(r'(多少.*订单|订单.*数|几个订单|订单量)', question_lower):
        return _get_order_count_answer(restaurant_id)
    
    # 模式5: 菜品收入排行/哪个菜赚钱
    if re.search(r'(哪.*菜.*赚|收入.*排|利润.*高|最.*钱.*菜)', question_lower):
        return _get_revenue_ranking_answer(restaurant_id)
    
    return None


def _get_top_consumers_answer(restaurant_id: int) -> str:
    """获取顶级消费者的规则答案"""
    top_consumers = db.session.query(
        User.username,
        func.sum(Order.total_amount).label('total_spent'),
        func.count(Order.id).label('order_count')
    ).join(Order, Order.user_id == User.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).group_by(User.id).order_by(desc('total_spent')).limit(5).all()
    
    if not top_consumers:
        return "目前还没有已支付的订单数据，暂时无法确定VIP客户。"
    
    lines = ["根据已支付订单统计，您的顶级客户是：\n"]
    for i, c in enumerate(top_consumers, 1):
        lines.append(f"{i}. **{c.username}** - 累计消费 ¥{c.total_spent:.2f}，共下单 {c.order_count} 次")
    
    lines.append("\n**建议**：")
    lines.append("1. 为这些VIP客户提供专属优惠或会员特权")
    lines.append("2. 分析他们的点餐偏好，优化菜品供应")
    lines.append("3. 通过他们的反馈持续改进服务质量")
    
    return "\n".join(lines)


def _get_top_dishes_answer(restaurant_id: int) -> str:
    """获取畅销菜品的规则答案"""
    top_dishes = db.session.query(
        Dish.name,
        func.sum(OrderItem.quantity).label('total_qty')
    ).join(OrderItem, Dish.id == OrderItem.dish_id
    ).join(Order, OrderItem.order_id == Order.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).group_by(Dish.id).order_by(desc('total_qty')).limit(5).all()
    
    if not top_dishes:
        return "目前还没有已支付的订单数据，暂时无法确定畅销菜品。"
    
    lines = ["根据已支付订单统计，您的畅销菜品排行是：\n"]
    for i, d in enumerate(top_dishes, 1):
        lines.append(f"{i}. **{d.name}** - 累计售出 {int(d.total_qty)} 份")
    
    lines.append("\n**建议**：")
    lines.append("1. 确保畅销菜品的原料供应充足稳定")
    lines.append("2. 考虑推出畅销菜品的套餐组合")
    lines.append("3. 在菜单显眼位置标注热销标识")
    
    return "\n".join(lines)


def _get_revenue_answer(restaurant_id: int) -> str:
    """获取总营收的规则答案"""
    result = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0).label('revenue'),
        func.count(Order.id).label('order_count')
    ).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).first()
    
    revenue = float(result.revenue or 0)
    order_count = result.order_count
    
    if order_count == 0:
        return "目前还没有已支付的订单，总营收为 ¥0.00。"
    
    avg_order = revenue / order_count if order_count > 0 else 0
    
    return f"""根据已支付订单统计：

- **总营收**：¥{revenue:.2f}
- **订单数**：{order_count} 单
- **平均客单价**：¥{avg_order:.2f}

**建议**：
1. 如果客单价较低，可考虑推出套餐组合提高单价
2. 设置满减活动鼓励顾客多点餐
3. 持续关注营收趋势，及时调整经营策略"""


def _get_order_count_answer(restaurant_id: int) -> str:
    """获取订单数的规则答案"""
    count = Order.query.filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).count()
    
    return f"您的餐厅目前共有 **{count}** 个已支付订单。"


def _get_revenue_ranking_answer(restaurant_id: int) -> str:
    """获取菜品收入排行的规则答案"""
    rankings = db.session.query(
        Dish.name,
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue'),
        func.sum(OrderItem.quantity).label('qty')
    ).join(OrderItem, Dish.id == OrderItem.dish_id
    ).join(Order, OrderItem.order_id == Order.id).filter(
        Order.restaurant_id == restaurant_id,
        Order.status == 'PAID'
    ).group_by(Dish.id).order_by(desc('revenue')).limit(5).all()
    
    if not rankings:
        return "目前还没有已支付的订单数据，暂时无法确定菜品收入排行。"
    
    lines = ["根据已支付订单统计，菜品收入排行是：\n"]
    for i, r in enumerate(rankings, 1):
        lines.append(f"{i}. **{r.name}** - 收入 ¥{float(r.revenue):.2f}（售出 {int(r.qty)} 份）")
    
    return "\n".join(lines)


def try_rule_answer_dish(question: str, dish_id: int) -> Optional[str]:
    """
    尝试使用规则匹配回答菜品问答问题
    
    对于常见的菜品相关问题，直接通过SQL查询返回答案。
    
    Args:
        question: 用户问题
        dish_id: 菜品ID
        
    Returns:
        规则匹配的答案，如果没有匹配则返回None
    """
    dish = Dish.query.get(dish_id)
    if not dish:
        return None
    
    question_lower = question.lower()
    
    # 模式1: 价格/多少钱
    if re.search(r'(多少钱|什么价|价格|几块|几元)', question_lower):
        return f"「{dish.name}」的价格是 **¥{float(dish.price):.2f}** 元。"
    
    # 模式2: 销量/卖了多少
    if re.search(r'(销量|卖了.*多少|多少份|销售.*情况)', question_lower):
        return _get_dish_sales_answer(dish)
    
    # 模式3: 谁点过/哪些人买过
    if re.search(r'(谁点过|谁买过|哪些人|谁.*吃过)', question_lower):
        return _get_dish_buyers_answer(dish)
    
    # 模式4: 介绍/是什么
    if re.search(r'(介绍|是什么|详情|描述)', question_lower) and dish.description:
        return f"**{dish.name}**\n\n{dish.description}\n\n价格：¥{float(dish.price):.2f}"
    
    return None


def _get_dish_sales_answer(dish: Dish) -> str:
    """获取菜品销量的规则答案"""
    stats = db.session.query(
        func.coalesce(func.sum(OrderItem.quantity), 0).label('total_qty'),
        func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label('total_revenue')
    ).join(Order, OrderItem.order_id == Order.id).filter(
        OrderItem.dish_id == dish.id,
        Order.status == 'PAID'
    ).first()
    
    qty = int(stats.total_qty or 0)
    revenue = float(stats.total_revenue or 0)
    
    if qty == 0:
        return f"「{dish.name}」目前还没有销售记录。快来尝试第一个下单吧！"
    
    return f"「{dish.name}」的销售情况：\n\n- 累计售出 **{qty}** 份\n- 累计收入 **¥{revenue:.2f}**\n\n是一款很受欢迎的菜品！"


def _get_dish_buyers_answer(dish: Dish) -> str:
    """获取菜品购买者的规则答案"""
    buyers = db.session.query(
        User.username,
        func.sum(OrderItem.quantity).label('qty')
    ).join(Order, Order.user_id == User.id
    ).join(OrderItem, OrderItem.order_id == Order.id).filter(
        OrderItem.dish_id == dish.id,
        Order.status == 'PAID'
    ).group_by(User.id).order_by(desc('qty')).limit(10).all()
    
    if not buyers:
        return f"「{dish.name}」目前还没有人购买过。成为第一个品尝的人吧！"
    
    buyer_list = "、".join([f"{b.username}（{int(b.qty)}份）" for b in buyers[:5]])
    total_buyers = len(buyers)
    
    return f"购买过「{dish.name}」的顾客有 **{total_buyers}** 位，包括：{buyer_list}。"


# ============================================================
# 主要接口函数
# ============================================================

def answer_manager_question(
    current_user,
    restaurant_id: int,
    question: str,
    chat_history: List[Dict[str, str]],
    model_override: Optional[str] = None
) -> Tuple[str, List[Dict[str, str]]]:
    """
    回答经营顾问问题
    
    流程：
    1. 尝试规则匹配
    2. 规则匹配失败则调用LLM
    
    Args:
        current_user: 当前用户对象
        restaurant_id: 餐厅ID
        question: 用户问题
        chat_history: 对话历史
        model_override: 可选的模型覆盖（如 'deepseek-reasoner'）
        
    Returns:
        (answer, updated_chat_history) 元组
    """
    # 首先检查API是否配置
    if not deepseek_client.is_api_configured():
        return ("智能问答功能未配置，请联系管理员设置 DEEPSEEK_API_KEY。", chat_history)
    
    # 尝试规则匹配
    rule_answer = try_rule_answer_manager(question, restaurant_id)
    if rule_answer:
        # 规则匹配成功，更新历史并返回
        new_history = chat_history.copy()
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": rule_answer})
        return (rule_answer, _trim_history(new_history))
    
    # 规则匹配失败，使用LLM
    try:
        # 构建数据快照
        snapshot = build_restaurant_snapshot(restaurant_id)
        context_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
        
        # 获取系统提示词
        system_prompt = qa_prompts.get_manager_system_prompt(context_json)
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": question})
        
        # 调用LLM
        # 如果指定了模型覆盖，临时设置环境变量（实际项目中可能需要更优雅的方式）
        original_model = os.environ.get('DEEPSEEK_MODEL', '')
        if model_override:
            os.environ['DEEPSEEK_MODEL'] = model_override
        
        try:
            answer = deepseek_client.call_chat_completion(
                messages=messages,
                temperature=0.6,
                max_tokens=1000
            )
        finally:
            # 恢复原始模型设置
            if model_override:
                if original_model:
                    os.environ['DEEPSEEK_MODEL'] = original_model
                else:
                    os.environ.pop('DEEPSEEK_MODEL', None)
        
        # 更新历史
        new_history = chat_history.copy()
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": answer})
        
        return (answer, _trim_history(new_history))
        
    except Exception as e:
        error_msg = deepseek_client.get_error_message(e)
        return (error_msg, chat_history)


def answer_dish_question(
    current_user,
    dish_id: int,
    question: str,
    chat_history: List[Dict[str, str]],
    model_override: Optional[str] = None
) -> Tuple[str, List[Dict[str, str]]]:
    """
    回答菜品问答问题
    
    流程：
    1. 检查是否询问其他菜品
    2. 尝试规则匹配
    3. 规则匹配失败则调用LLM
    
    Args:
        current_user: 当前用户对象
        dish_id: 当前菜品ID
        question: 用户问题
        chat_history: 对话历史
        model_override: 可选的模型覆盖
        
    Returns:
        (answer, updated_chat_history) 元组
    """
    # 首先检查API是否配置
    if not deepseek_client.is_api_configured():
        return ("智能问答功能未配置，请联系管理员设置 DEEPSEEK_API_KEY。", chat_history)
    
    dish = Dish.query.get(dish_id)
    if not dish:
        return ("抱歉，找不到该菜品信息。", chat_history)
    
    # 检查是否询问其他菜品
    target_dish_id = dish_id
    target_dish_name = dish.name
    
    if qa_matcher.is_asking_about_other_dish(question, dish.name):
        # 尝试提取并匹配其他菜品
        extracted_name = qa_matcher.extract_dish_name_from_question(question)
        if extracted_name:
            match_result = qa_matcher.fuzzy_match_dish_name(
                extracted_name, 
                dish.restaurant_id
            )
            if match_result:
                target_dish_id, target_dish_name, _ = match_result
    
    # 尝试规则匹配
    rule_answer = try_rule_answer_dish(question, target_dish_id)
    if rule_answer:
        new_history = chat_history.copy()
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": rule_answer})
        return (rule_answer, _trim_history(new_history))
    
    # 规则匹配失败，使用LLM
    try:
        # 构建数据快照
        snapshot = build_dish_snapshot(target_dish_id)
        context_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
        
        # 获取系统提示词
        if target_dish_id != dish_id:
            # 用户在询问其他菜品
            system_prompt = qa_prompts.get_dish_cross_query_prompt(
                context_json, 
                target_dish_name
            )
        else:
            system_prompt = qa_prompts.get_dish_system_prompt(
                context_json, 
                target_dish_name
            )
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": question})
        
        # 调用LLM
        answer = deepseek_client.call_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        # 更新历史
        new_history = chat_history.copy()
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": answer})
        
        return (answer, _trim_history(new_history))
        
    except Exception as e:
        error_msg = deepseek_client.get_error_message(e)
        return (error_msg, chat_history)


def _trim_history(history: List[Dict[str, str]], max_turns: int = 10) -> List[Dict[str, str]]:
    """
    修剪对话历史，保持最近的N轮对话
    
    每轮对话包含1条user消息和1条assistant消息。
    
    Args:
        history: 对话历史列表
        max_turns: 最大轮数
        
    Returns:
        修剪后的历史列表
    """
    max_messages = max_turns * 2  # 每轮2条消息
    if len(history) > max_messages:
        return history[-max_messages:]
    return history
