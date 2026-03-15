# -*- coding: utf-8 -*-
"""
订餐相关路由模块
处理餐厅浏览、菜品查看、购物车、结算、智能问答等请求
"""

import flask
import flask_login
import sqlalchemy
import decimal

from app.order import order_bp
import app.extensions as extensions
from app.models import Restaurant, Category, Dish, Order, OrderItem, Blacklist, User
import app.constants as constants
from app.ai import deepseek_client
from app.ai import qa_engine


# 聊天历史最大轮次
MAX_CHAT_TURNS = 10


def is_user_blacklisted(restaurant_id, user_id):
    """
    检查用户是否被餐厅拉黑
    
    参数:
        restaurant_id: 餐厅ID
        user_id: 用户ID
        
    返回:
        bool: 是否被拉黑
    """
    blacklist_entry = Blacklist.query.filter_by(
        restaurant_id=restaurant_id,
        user_id=user_id
    ).first()
    return blacklist_entry is not None


def get_cart():
    """
    获取当前会话中的购物车数据
    
    返回:
        dict: 购物车数据 {"restaurant_id": int, "items": {dish_id: qty}}
    """
    return flask.session.get('cart', {'restaurant_id': None, 'items': {}})


def save_cart(cart):
    """
    保存购物车数据到会话
    
    参数:
        cart: 购物车字典
    """
    flask.session['cart'] = cart
    flask.session.modified = True


def clear_cart():
    """
    清空购物车
    """
    flask.session['cart'] = {'restaurant_id': None, 'items': {}}
    flask.session.modified = True


# 常量定义（如果原文件中没有的话）
MAX_CHAT_TURNS = 10


def get_ai_chat_history(chat_key: str) -> list:
    """
    从session获取指定key的AI聊天历史

    Args:
        chat_key: 聊天会话标识，如 'dish:123'

    Returns:
        聊天历史列表
    """
    import flask
    if 'ai_chat' not in flask.session:
        flask.session['ai_chat'] = {}
    if 'order' not in flask.session['ai_chat']:
        flask.session['ai_chat']['order'] = {}
    return flask.session['ai_chat']['order'].get(chat_key, [])


def save_ai_chat_history(chat_key: str, history: list) -> None:
    """
    保存AI聊天历史到session

    Args:
        chat_key: 聊天会话标识
        history: 聊天历史列表
    """
    import flask
    if 'ai_chat' not in flask.session:
        flask.session['ai_chat'] = {}
    if 'order' not in flask.session['ai_chat']:
        flask.session['ai_chat']['order'] = {}
    flask.session['ai_chat']['order'][chat_key] = history
    flask.session.modified = True


def clear_ai_chat_history(chat_key):
    """
    清空指定的AI聊天历史
    
    参数:
        chat_key: 聊天标识
    """
    ai_chat = flask.session.get('ai_chat', {})
    order_chats = ai_chat.get('order', {})
    if chat_key in order_chats:
        del order_chats[chat_key]
        ai_chat['order'] = order_chats
        flask.session['ai_chat'] = ai_chat
        flask.session.modified = True


@order_bp.route('/')
@order_bp.route('/home')
@flask_login.login_required
def home():
    """
    订餐首页：显示所有餐厅列表，按销售额降序排列
    销售额 = 该餐厅所有已支付订单的总金额之和
    """
    # 使用子查询计算每个餐厅的销售额
    # 只统计状态为PAID的订单
    sales_subquery = extensions.db.session.query(
        Order.restaurant_id,
        sqlalchemy.func.coalesce(
            sqlalchemy.func.sum(Order.total_amount), 
            decimal.Decimal('0')
        ).label('total_sales')
    ).filter(
        Order.status == 'PAID'
    ).group_by(
        Order.restaurant_id
    ).subquery()
    
    # 左连接餐厅表和销售额子查询，确保没有订单的餐厅也能显示
    restaurants_with_sales = extensions.db.session.query(
        Restaurant,
        sqlalchemy.func.coalesce(sales_subquery.c.total_sales, decimal.Decimal('0')).label('sales')
    ).outerjoin(
        sales_subquery,
        Restaurant.id == sales_subquery.c.restaurant_id
    ).order_by(
        sqlalchemy.desc('sales')
    ).all()
    
    return flask.render_template(
        'order/restaurants.html',
        restaurants_with_sales=restaurants_with_sales
    )


@order_bp.route('/restaurant/<int:restaurant_id>')
@flask_login.login_required
def restaurant(restaurant_id):
    """
    餐厅菜单页面：显示分类和菜品
    如果用户被拉黑，显示拒绝页面
    
    参数:
        restaurant_id: 餐厅ID
    """
    # 查询餐厅
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    # 检查黑名单
    if is_user_blacklisted(restaurant_id, flask_login.current_user.id):
        return flask.render_template(
            'order/blocked.html',
            restaurant=restaurant
        )
    
    # 查询餐厅的所有分类和菜品
    categories_data = []
    for cat_name in constants.FIXED_CATEGORIES:
        category = Category.query.filter_by(
            restaurant_id=restaurant_id,
            name=cat_name
        ).first()
        
        if category:
            dishes = Dish.query.filter_by(category_id=category.id).all()
            categories_data.append({
                'category': category,
                'name_internal': cat_name,
                'name_display': constants.CATEGORY_LABELS.get(cat_name, cat_name),
                'dishes': dishes
            })
    
    # 获取购物车信息
    cart = get_cart()
    cart_restaurant_id = cart.get('restaurant_id')
    cart_items = cart.get('items', {})
    
    return flask.render_template(
        'order/restaurant.html',
        restaurant=restaurant,
        categories_data=categories_data,
        category_labels=constants.CATEGORY_LABELS,
        cart_restaurant_id=cart_restaurant_id,
        cart_items=cart_items
    )


@order_bp.route('/dish/<int:dish_id>')
@flask_login.login_required
def dish_detail(dish_id):
    """
    菜品详情页面
    
    参数:
        dish_id: 菜品ID
    """
    # 查询菜品
    dish = Dish.query.get_or_404(dish_id)
    restaurant = Restaurant.query.get_or_404(dish.restaurant_id)
    
    # 检查黑名单
    if is_user_blacklisted(restaurant.id, flask_login.current_user.id):
        return flask.render_template(
            'order/blocked.html',
            restaurant=restaurant
        )
    
    return flask.render_template(
        'order/dish.html',
        dish=dish,
        restaurant=restaurant
    )


@order_bp.route('/cart/add/<int:dish_id>', methods=['POST'])
@flask_login.login_required
def cart_add(dish_id):
    """
    添加菜品到购物车
    
    参数:
        dish_id: 菜品ID
    """
    # 查询菜品
    dish = Dish.query.get_or_404(dish_id)
    restaurant_id = dish.restaurant_id
    
    # 检查黑名单
    if is_user_blacklisted(restaurant_id, flask_login.current_user.id):
        flask.flash('你已被该餐厅拉入黑名单，无法点餐。', 'danger')
        return flask.redirect(flask.url_for('order.home'))
    
    # 获取购物车
    cart = get_cart()
    cart_restaurant_id = cart.get('restaurant_id')
    cart_items = cart.get('items', {})
    
    # 检查是否是同一餐厅
    if cart_restaurant_id is not None and cart_restaurant_id != restaurant_id:
        # 购物车已有其他餐厅的菜品
        flask.flash('你的餐桌中已有其他餐厅的菜品，请先结算或清空餐桌。', 'warning')
        return flask.redirect(flask.url_for('order.restaurant', restaurant_id=restaurant_id))
    
    # 添加到购物车
    dish_id_str = str(dish_id)
    if dish_id_str in cart_items:
        cart_items[dish_id_str] += 1
    else:
        cart_items[dish_id_str] = 1
    
    cart['restaurant_id'] = restaurant_id
    cart['items'] = cart_items
    save_cart(cart)
    
    flask.flash(f'已将「{dish.name}」加入餐桌', 'success')
    return flask.redirect(flask.url_for('order.restaurant', restaurant_id=restaurant_id))


@order_bp.route('/cart/set/<int:dish_id>', methods=['POST'])
@flask_login.login_required
def cart_set(dish_id):
    """
    设置购物车中菜品的数量
    数量为0时移除该菜品
    
    参数:
        dish_id: 菜品ID
    """
    # 获取数量参数
    try:
        qty = int(flask.request.form.get('qty', 0))
    except ValueError:
        qty = 0
    
    # 获取购物车
    cart = get_cart()
    cart_items = cart.get('items', {})
    dish_id_str = str(dish_id)
    
    if qty <= 0:
        # 移除菜品
        if dish_id_str in cart_items:
            del cart_items[dish_id_str]
    else:
        # 设置数量
        cart_items[dish_id_str] = qty
    
    # 如果购物车为空，清除餐厅ID
    if not cart_items:
        cart['restaurant_id'] = None
    
    cart['items'] = cart_items
    save_cart(cart)
    
    return flask.redirect(flask.url_for('order.cart'))


@order_bp.route('/cart/clear', methods=['POST'])
@flask_login.login_required
def cart_clear():
    """
    清空购物车
    """
    clear_cart()
    flask.flash('餐桌已清空', 'info')
    return flask.redirect(flask.url_for('order.home'))


@order_bp.route('/cart')
@flask_login.login_required
def cart():
    """
    我的餐桌（购物车）页面
    """
    cart_data = get_cart()
    cart_restaurant_id = cart_data.get('restaurant_id')
    cart_items = cart_data.get('items', {})
    
    # 如果购物车为空
    if not cart_restaurant_id or not cart_items:
        return flask.render_template(
            'order/cart.html',
            restaurant=None,
            items=[],
            total=decimal.Decimal('0')
        )
    
    # 查询餐厅
    restaurant = Restaurant.query.get(cart_restaurant_id)
    if not restaurant:
        clear_cart()
        return flask.render_template(
            'order/cart.html',
            restaurant=None,
            items=[],
            total=decimal.Decimal('0')
        )
    
    # 构建购物车项目列表
    items = []
    total = decimal.Decimal('0')
    
    for dish_id_str, qty in cart_items.items():
        try:
            dish_id = int(dish_id_str)
            dish = Dish.query.get(dish_id)
            if dish and dish.restaurant_id == cart_restaurant_id:
                line_total = dish.price * qty
                items.append({
                    'dish': dish,
                    'qty': qty,
                    'line_total': line_total
                })
                total += line_total
        except (ValueError, TypeError):
            continue
    
    return flask.render_template(
        'order/cart.html',
        restaurant=restaurant,
        items=items,
        total=total
    )


@order_bp.route('/checkout', methods=['POST'])
@flask_login.login_required
def checkout():
    """
    结算/付款
    创建订单并清空购物车
    """
    cart_data = get_cart()
    cart_restaurant_id = cart_data.get('restaurant_id')
    cart_items = cart_data.get('items', {})
    
    # 检查购物车是否为空
    if not cart_restaurant_id or not cart_items:
        flask.flash('餐桌是空的，请先添加菜品', 'warning')
        return flask.redirect(flask.url_for('order.home'))
    
    # 查询餐厅
    restaurant = Restaurant.query.get(cart_restaurant_id)
    if not restaurant:
        flask.flash('餐厅不存在', 'danger')
        clear_cart()
        return flask.redirect(flask.url_for('order.home'))
    
    # 检查黑名单
    if is_user_blacklisted(cart_restaurant_id, flask_login.current_user.id):
        flask.flash('你已被该餐厅拉入黑名单，无法点餐。', 'danger')
        clear_cart()
        return flask.redirect(flask.url_for('order.home'))
    
    try:
        # 创建订单
        order = Order(
            restaurant_id=cart_restaurant_id,
            user_id=flask_login.current_user.id,
            total_amount=decimal.Decimal('0'),
            status='PAID'
        )
        extensions.db.session.add(order)
        extensions.db.session.flush()  # 获取订单ID
        
        # 创建订单项
        total_amount = decimal.Decimal('0')
        order_items_data = []
        
        for dish_id_str, qty in cart_items.items():
            try:
                dish_id = int(dish_id_str)
                dish = Dish.query.get(dish_id)
                
                # 验证菜品存在且属于当前餐厅
                if not dish or dish.restaurant_id != cart_restaurant_id:
                    continue
                
                line_total = dish.price * qty
                total_amount += line_total
                
                order_item = OrderItem(
                    order_id=order.id,
                    dish_id=dish_id,
                    qty=qty,
                    unit_price=dish.price,
                    line_total=line_total
                )
                extensions.db.session.add(order_item)
                
                order_items_data.append({
                    'dish': dish,
                    'qty': qty,
                    'unit_price': dish.price,
                    'line_total': line_total
                })
                
            except (ValueError, TypeError):
                continue
        
        # 更新订单总金额
        order.total_amount = total_amount
        extensions.db.session.commit()
        
        # 清空购物车
        clear_cart()
        
        return flask.render_template(
            'order/paid.html',
            order=order,
            restaurant=restaurant,
            order_items=order_items_data,
            total_amount=total_amount
        )
        
    except Exception as e:
        extensions.db.session.rollback()
        flask.flash(f'结算失败，请稍后重试。错误: {str(e)}', 'danger')
        return flask.redirect(flask.url_for('order.cart'))


@order_bp.route('/ask/<int:dish_id>', methods=['GET', 'POST'])
@flask_login.login_required
def ask(dish_id):
    """
    菜品智能问答页面

    使用QA引擎回答关于菜品的问题，支持：
    - 规则匹配的即时回答
    - LLM生成的智能回答
    - 跨菜品查询
    """
    import flask
    from flask import render_template, request, flash, redirect, url_for
    from flask_login import current_user
    from app.models import Dish
    from app.ai import deepseek_client
    from app.ai import qa_engine  # 新增导入

    # 获取菜品信息
    dish = Dish.query.get_or_404(dish_id)

    # 检查API是否配置
    api_configured = deepseek_client.is_api_configured()

    # 获取聊天历史
    chat_key = f"dish:{dish_id}"
    chat_history = get_ai_chat_history(chat_key)

    # 处理POST请求
    if request.method == 'POST' and api_configured:
        user_question = request.form.get('message', '').strip()

        if user_question:
            # 使用QA引擎回答问题
            answer, updated_history = qa_engine.answer_dish_question(
                current_user=current_user,
                dish_id=dish_id,
                question=user_question,
                chat_history=chat_history,
                model_override=None  # 使用默认模型，或设为 'deepseek-chat'
            )

            # 保存更新后的历史
            save_ai_chat_history(chat_key, updated_history)
            chat_history = updated_history

    # 构建显示用的聊天记录
    display_messages = []
    for msg in chat_history:
        display_messages.append({
            'role': msg['role'],
            'content': msg['content'],
            'is_user': msg['role'] == 'user'
        })

    return render_template(
        'order/ask.html',
        dish=dish,
        api_configured=api_configured,
        chat_history=display_messages
    )


@order_bp.route('/ask/<int:dish_id>/clear', methods=['POST'])
@flask_login.login_required
def clear_dish_chat(dish_id):
    """清除指定菜品的聊天历史"""
    import flask
    from flask import redirect, url_for, flash

    chat_key = f"dish:{dish_id}"
    if 'ai_chat' in flask.session and 'order' in flask.session['ai_chat']:
        flask.session['ai_chat']['order'].pop(chat_key, None)
        flask.session.modified = True

    flash('聊天记录已清除', 'success')
    return redirect(url_for('order.ask', dish_id=dish_id))


def _build_dish_system_prompt(dish, restaurant):
    """
    构建菜品问答的系统提示词
    
    参数:
        dish: 当前菜品对象
        restaurant: 餐厅对象
        
    返回:
        str: 系统提示词
    """
    # 获取餐厅所有菜品简要信息
    all_dishes = Dish.query.filter_by(restaurant_id=restaurant.id).all()
    other_dishes_info = []
    for d in all_dishes:
        if d.id != dish.id:
            other_dishes_info.append(f"- {d.name}: ¥{d.price}，{d.description[:50]}...")
    
    other_dishes_text = "\n".join(other_dishes_info) if other_dishes_info else "（暂无其他菜品）"
    
    system_prompt = f"""你是「{restaurant.name}」餐厅的智能点餐助手。你的主要任务是回答关于菜品的问题。

【当前菜品信息】
- 菜品名称：{dish.name}
- 价格：¥{dish.price}
- 描述：{dish.description}

【本餐厅其他菜品】
{other_dishes_text}

【回答规则】
1. 请用中文回答所有问题
2. 默认情况下，请围绕当前菜品「{dish.name}」进行回答
3. 如果用户明确询问其他菜品，可以参考上面提供的菜品信息回答
4. 回答要简洁、专业、友好
5. 如果无法从提供的数据中确认某个信息，请诚实地说"我暂时无法从当前数据确认这个信息"
6. 不要编造菜品不存在的信息，如食材详情、营养成分等（除非描述中有提及）
7. 可以提供点餐建议和搭配推荐

请开始为顾客提供帮助！"""
    
    return system_prompt
