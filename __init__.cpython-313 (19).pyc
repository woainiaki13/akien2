# -*- coding: utf-8 -*-
"""
餐厅管理相关路由模块
处理餐厅创建、菜品管理、黑名单管理、数据分析、智能顾问等请求
"""

import flask
import flask_login
import sqlalchemy
import decimal

from app.manager import manager_bp
from app.manager.forms import RestaurantCreateForm, DishCreateForm
import app.extensions as extensions
from app.models import Restaurant, Category, Dish, User, Order, OrderItem, Blacklist
import app.constants as constants
from app.ai import deepseek_client
from app.ai import qa_engine


# 经营顾问聊天历史最大轮次
MAX_ADVISOR_TURNS = 10


def _get_owner_restaurant():
    """
    获取当前登录用户的餐厅
    如果用户没有餐厅，返回None
    
    返回:
        Restaurant或None
    """
    return Restaurant.query.filter_by(
        owner_user_id=flask_login.current_user.id
    ).first()


# 常量定义
MAX_ADVISOR_TURNS = 10


def get_advisor_chat_history() -> list:
    """
    从session获取经营顾问的聊天历史

    Returns:
        聊天历史列表
    """
    import flask
    if 'ai_chat' not in flask.session:
        flask.session['ai_chat'] = {}
    if 'manager' not in flask.session['ai_chat']:
        flask.session['ai_chat']['manager'] = {}
    return flask.session['ai_chat']['manager'].get('advisor', [])


def save_advisor_chat_history(history: list) -> None:
    """
    保存经营顾问聊天历史到session

    Args:
        history: 聊天历史列表
    """
    import flask
    if 'ai_chat' not in flask.session:
        flask.session['ai_chat'] = {}
    if 'manager' not in flask.session['ai_chat']:
        flask.session['ai_chat']['manager'] = {}
    flask.session['ai_chat']['manager']['advisor'] = history
    flask.session.modified = True

@manager_bp.route('/advisor/clear', methods=['POST'])
@flask_login.login_required
def clear_advisor_chat():
    """清除经营顾问的聊天历史"""
    import flask
    from flask import redirect, url_for, flash

    if 'ai_chat' in flask.session and 'manager' in flask.session['ai_chat']:
        flask.session['ai_chat']['manager'].pop('advisor', None)
        flask.session.modified = True

    flash('聊天记录已清除', 'success')
    return redirect(url_for('manager.advisor'))


@manager_bp.route('/')
@manager_bp.route('/home')
@flask_login.login_required
def home():
    """
    餐厅管理首页
    如果用户没有餐厅，重定向到创建餐厅页面
    如果有餐厅，显示仪表盘（类别和菜品列表）
    """
    # 查询当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=flask_login.current_user.id).first()
    
    if not restaurant:
        # 没有餐厅，重定向到创建页面
        flask.flash(constants.UI_TEXT['restaurant']['no_restaurant'], 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 查询餐厅的所有类别和菜品
    categories = Category.query.filter_by(restaurant_id=restaurant.id).all()
    
    # 为每个类别组织菜品数据
    category_dishes = {}
    for category in categories:
        dishes = Dish.query.filter_by(category_id=category.id).all()
        category_dishes[category.name] = {
            'category': category,
            'dishes': dishes,
            'label': constants.CATEGORY_LABELS.get(category.name, category.name)
        }
    
    return flask.render_template(
        'manager/dashboard.html',
        restaurant=restaurant,
        category_dishes=category_dishes,
        fixed_categories=constants.FIXED_CATEGORIES,
        ui_text=constants.UI_TEXT
    )


@manager_bp.route('/create-restaurant', methods=['GET', 'POST'])
@flask_login.login_required
def create_restaurant():
    """
    创建餐厅视图
    GET: 显示创建表单
    POST: 处理创建请求
    """
    from app.utils.images import save_logo
    
    # 检查用户是否已有餐厅
    existing_restaurant = Restaurant.query.filter_by(
        owner_user_id=flask_login.current_user.id
    ).first()
    
    if existing_restaurant:
        flask.flash('您已经创建过餐厅了。', 'warning')
        return flask.redirect(flask.url_for('manager.home'))
    
    form = RestaurantCreateForm()
    
    if form.validate_on_submit():
        try:
            # 获取Logo上传目录
            upload_dir = flask.current_app.config['LOGO_UPLOAD_FOLDER']
            max_size = flask.current_app.config['LOGO_MAX_SIZE']
            
            # 保存Logo并获取相对路径
            logo_path = save_logo(form.logo.data, upload_dir, max_size)
            
            # 创建餐厅
            restaurant = Restaurant(
                name=form.name.data,
                logo_path=logo_path,
                owner_user_id=flask_login.current_user.id
            )
            
            extensions.db.session.add(restaurant)
            extensions.db.session.flush()  # 获取restaurant.id
            
            # 为餐厅创建固定的4个类别
            for category_name in constants.FIXED_CATEGORIES:
                category = Category(
                    restaurant_id=restaurant.id,
                    name=category_name
                )
                extensions.db.session.add(category)
            
            extensions.db.session.commit()
            
            flask.flash(constants.UI_TEXT['restaurant']['create_success'], 'success')
            return flask.redirect(flask.url_for('manager.home'))
            
        except ValueError as e:
            # Logo处理错误
            flask.flash(str(e), 'danger')
        except Exception as e:
            # 其他错误，回滚数据库事务
            extensions.db.session.rollback()
            flask.flash(f"{constants.UI_TEXT['restaurant']['create_failed']} 错误: {str(e)}", 'danger')
    
    return flask.render_template(
        'manager/create_restaurant.html',
        form=form,
        ui_text=constants.UI_TEXT
    )


@manager_bp.route('/add-dish/<string:category_name>', methods=['GET', 'POST'])
@flask_login.login_required
def add_dish(category_name):
    """
    添加菜品视图
    GET: 显示添加表单
    POST: 处理添加请求
    
    参数:
        category_name: 类别名称（英文：Drink/Dish/Staple/Other）
    """
    from app.utils.images import save_dish_image
    
    # 验证类别名称是否有效
    if category_name not in constants.FIXED_CATEGORIES:
        flask.flash('无效的类别', 'danger')
        return flask.redirect(flask.url_for('manager.home'))
    
    # 查询当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=flask_login.current_user.id).first()
    
    if not restaurant:
        flask.flash(constants.UI_TEXT['restaurant']['no_restaurant'], 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 查询类别
    category = Category.query.filter_by(
        restaurant_id=restaurant.id,
        name=category_name
    ).first()
    
    if not category:
        flask.flash('类别不存在', 'danger')
        return flask.redirect(flask.url_for('manager.home'))
    
    form = DishCreateForm()
    
    if form.validate_on_submit():
        try:
            # 获取菜品图片上传目录
            upload_dir = flask.current_app.config['DISH_UPLOAD_FOLDER']
            max_size = flask.current_app.config['DISH_IMAGE_MAX_SIZE']
            
            # 保存菜品图片并获取相对路径
            image_path = save_dish_image(form.image.data, upload_dir, max_size)
            
            # 创建菜品
            dish = Dish(
                restaurant_id=restaurant.id,
                category_id=category.id,
                name=form.name.data,
                price=form.price.data,
                description=form.description.data,
                image_path=image_path
            )
            
            extensions.db.session.add(dish)
            extensions.db.session.commit()
            
            flask.flash(constants.UI_TEXT['dish']['add_success'], 'success')
            return flask.redirect(flask.url_for('manager.home'))
            
        except ValueError as e:
            # 图片处理错误
            flask.flash(str(e), 'danger')
        except Exception as e:
            # 其他错误，回滚数据库事务
            extensions.db.session.rollback()
            flask.flash(f"{constants.UI_TEXT['dish']['add_failed']} 错误: {str(e)}", 'danger')
    
    return flask.render_template(
        'manager/add_dish.html',
        form=form,
        category=category,
        category_label=constants.CATEGORY_LABELS.get(category_name, category_name),
        ui_text=constants.UI_TEXT
    )


@manager_bp.route('/delete-dish/<int:dish_id>', methods=['POST'])
@flask_login.login_required
def delete_dish(dish_id):
    """
    删除菜品
    仅支持POST请求，包含CSRF保护
    级联删除相关的订单项
    
    参数:
        dish_id: 菜品ID
    """
    # 查询菜品
    dish = Dish.query.get_or_404(dish_id)
    
    # 验证菜品是否属于当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=flask_login.current_user.id).first()
    
    if not restaurant or dish.restaurant_id != restaurant.id:
        flask.flash('无权删除此菜品', 'danger')
        return flask.redirect(flask.url_for('manager.home'))
    
    try:
        # 删除菜品（级联删除相关的OrderItem记录）
        extensions.db.session.delete(dish)
        extensions.db.session.commit()
        
        flask.flash(constants.UI_TEXT['dish']['delete_success'], 'success')
    except Exception as e:
        extensions.db.session.rollback()
        flask.flash(f"{constants.UI_TEXT['dish']['delete_failed']} 错误: {str(e)}", 'danger')
    
    return flask.redirect(flask.url_for('manager.home'))


# ==================== 黑名单管理（Step-3） ====================

@manager_bp.route('/blacklist')
@flask_login.login_required
def blacklist():
    """
    黑名单管理页面
    显示当前餐厅的黑名单列表，并可以添加/移除用户
    """
    # 查询当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=flask_login.current_user.id).first()
    
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 查询当前黑名单
    blacklist_entries = Blacklist.query.filter_by(restaurant_id=restaurant.id).all()
    blacklisted_user_ids = [entry.user_id for entry in blacklist_entries]
    
    # 查询可以添加到黑名单的用户（有订单记录且未被拉黑的用户，排除餐厅老板自己）
    users_with_orders = extensions.db.session.query(User).join(
        Order, User.id == Order.user_id
    ).filter(
        Order.restaurant_id == restaurant.id,
        User.id != flask_login.current_user.id
    ).distinct().all()
    
    # 过滤掉已经在黑名单中的用户
    available_users = [u for u in users_with_orders if u.id not in blacklisted_user_ids]
    
    return flask.render_template(
        'manager/blacklist.html',
        restaurant=restaurant,
        blacklist_entries=blacklist_entries,
        available_users=available_users
    )


@manager_bp.route('/blacklist/add', methods=['POST'])
@flask_login.login_required
def blacklist_add():
    """
    添加用户到黑名单
    """
    # 查询当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=flask_login.current_user.id).first()
    
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 获取要拉黑的用户ID
    user_id = flask.request.form.get('user_id')
    if not user_id:
        flask.flash('请选择要拉黑的用户', 'warning')
        return flask.redirect(flask.url_for('manager.blacklist'))
    
    try:
        user_id = int(user_id)
    except ValueError:
        flask.flash('无效的用户ID', 'danger')
        return flask.redirect(flask.url_for('manager.blacklist'))
    
    # 检查用户是否存在
    user = User.query.get(user_id)
    if not user:
        flask.flash('用户不存在', 'danger')
        return flask.redirect(flask.url_for('manager.blacklist'))
    
    # 不能拉黑自己
    if user_id == flask_login.current_user.id:
        flask.flash('不能将自己加入黑名单', 'warning')
        return flask.redirect(flask.url_for('manager.blacklist'))
    
    # 检查是否已经在黑名单中
    existing = Blacklist.query.filter_by(
        restaurant_id=restaurant.id,
        user_id=user_id
    ).first()
    
    if existing:
        flask.flash('该用户已在黑名单中', 'warning')
        return flask.redirect(flask.url_for('manager.blacklist'))
    
    try:
        # 添加到黑名单
        blacklist_entry = Blacklist(
            restaurant_id=restaurant.id,
            user_id=user_id
        )
        extensions.db.session.add(blacklist_entry)
        extensions.db.session.commit()
        
        flask.flash(f'已将用户「{user.username}」加入黑名单', 'success')
    except Exception as e:
        extensions.db.session.rollback()
        flask.flash(f'操作失败: {str(e)}', 'danger')
    
    return flask.redirect(flask.url_for('manager.blacklist'))


@manager_bp.route('/blacklist/remove/<int:entry_id>', methods=['POST'])
@flask_login.login_required
def blacklist_remove(entry_id):
    """
    从黑名单中移除用户
    
    参数:
        entry_id: 黑名单记录ID
    """
    # 查询当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=flask_login.current_user.id).first()
    
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 查询黑名单记录
    entry = Blacklist.query.get_or_404(entry_id)
    
    # 验证是否属于当前餐厅
    if entry.restaurant_id != restaurant.id:
        flask.flash('无权操作', 'danger')
        return flask.redirect(flask.url_for('manager.blacklist'))
    
    try:
        username = entry.user.username
        extensions.db.session.delete(entry)
        extensions.db.session.commit()
        
        flask.flash(f'已将用户「{username}」移出黑名单', 'success')
    except Exception as e:
        extensions.db.session.rollback()
        flask.flash(f'操作失败: {str(e)}', 'danger')
    
    return flask.redirect(flask.url_for('manager.blacklist'))


# ==================== 数据分析（Step-4） ====================

@manager_bp.route('/stats/dishes')
@flask_login.login_required
def dish_stats():
    """
    菜品统计页面
    显示每道菜的销售数据：总份数、点过的消费者列表
    只统计已支付(PAID)的订单
    """
    # 验证餐厅所有权
    restaurant = _get_owner_restaurant()
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 查询所有菜品
    dishes = Dish.query.filter_by(restaurant_id=restaurant.id).all()
    
    # 为每道菜计算统计数据
    dish_stats_list = []
    
    for dish in dishes:
        # 查询该菜品的总份数（只统计PAID订单）
        total_qty_result = extensions.db.session.query(
            sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.qty), 0)
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.dish_id == dish.id,
            Order.status == 'PAID'
        ).scalar()
        
        total_qty = int(total_qty_result) if total_qty_result else 0
        
        # 查询点过该菜品的消费者（去重，只统计PAID订单）
        consumers = extensions.db.session.query(User).join(
            Order, User.id == Order.user_id
        ).join(
            OrderItem, Order.id == OrderItem.order_id
        ).filter(
            OrderItem.dish_id == dish.id,
            Order.status == 'PAID'
        ).distinct().all()
        
        dish_stats_list.append({
            'dish': dish,
            'total_qty': total_qty,
            'consumer_count': len(consumers),
            'consumers': consumers
        })
    
    return flask.render_template(
        'manager/dish_stats.html',
        restaurant=restaurant,
        dish_stats=dish_stats_list
    )


@manager_bp.route('/consumers')
@flask_login.login_required
def consumers():
    """
    消费者列表页面
    显示所有在本餐厅消费过的用户，按总消费金额排序
    只统计已支付(PAID)的订单
    """
    # 验证餐厅所有权
    restaurant = _get_owner_restaurant()
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 获取排序参数（默认降序）
    sort_order = flask.request.args.get('sort', 'desc')
    if sort_order not in ('asc', 'desc'):
        sort_order = 'desc'
    
    # 查询消费者及其总消费金额（只统计PAID订单）
    consumers_query = extensions.db.session.query(
        User,
        sqlalchemy.func.coalesce(
            sqlalchemy.func.sum(Order.total_amount),
            decimal.Decimal('0')
        ).label('total_spend')
    ).join(
        Order, User.id == Order.user_id
    ).filter(
        Order.restaurant_id == restaurant.id,
        Order.status == 'PAID'
    ).group_by(User.id)
    
    # 应用排序
    if sort_order == 'desc':
        consumers_query = consumers_query.order_by(sqlalchemy.desc('total_spend'))
    else:
        consumers_query = consumers_query.order_by(sqlalchemy.asc('total_spend'))
    
    consumers_list = consumers_query.all()
    
    return flask.render_template(
        'manager/consumers.html',
        restaurant=restaurant,
        consumers=consumers_list,
        sort_order=sort_order
    )


@manager_bp.route('/consumers/<int:user_id>/history')
@flask_login.login_required
def consumer_history(user_id):
    """
    消费者订单历史页面
    显示某个消费者在本餐厅的消费记录（按菜品聚合）
    只统计已支付(PAID)的订单
    
    参数:
        user_id: 消费者用户ID
    """
    # 验证餐厅所有权
    restaurant = _get_owner_restaurant()
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 查询消费者
    consumer = User.query.get_or_404(user_id)
    
    # 查询该消费者在本餐厅的菜品消费聚合数据（只统计PAID订单）
    dish_summary = extensions.db.session.query(
        Dish,
        sqlalchemy.func.sum(OrderItem.qty).label('total_qty'),
        sqlalchemy.func.sum(OrderItem.line_total).label('total_amount')
    ).join(
        OrderItem, Dish.id == OrderItem.dish_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.restaurant_id == restaurant.id,
        Order.user_id == user_id,
        Order.status == 'PAID'
    ).group_by(Dish.id).all()
    
    # 计算总份数和总消费金额
    total_qty = sum(int(item[1]) for item in dish_summary) if dish_summary else 0
    total_amount = sum(item[2] for item in dish_summary) if dish_summary else decimal.Decimal('0')
    
    return flask.render_template(
        'manager/consumer_history.html',
        restaurant=restaurant,
        consumer=consumer,
        dish_summary=dish_summary,
        total_qty=total_qty,
        total_amount=total_amount
    )


@manager_bp.route('/reports')
@flask_login.login_required
def reports():
    """
    菜品报表页面
    显示饼图报表，支持按份数或按销售额两种模式
    只统计已支付(PAID)的订单
    """
    # 验证餐厅所有权
    restaurant = _get_owner_restaurant()
    if not restaurant:
        flask.flash('请先创建餐厅', 'warning')
        return flask.redirect(flask.url_for('manager.create_restaurant'))
    
    # 获取报表模式（默认按份数）
    mode = flask.request.args.get('mode', 'qty')
    if mode not in ('qty', 'amount'):
        mode = 'qty'
    
    # 查询各菜品的统计数据（只统计PAID订单）
    if mode == 'qty':
        # 按份数统计
        stats = extensions.db.session.query(
            Dish.name,
            sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.qty), 0).label('value')
        ).outerjoin(
            OrderItem, Dish.id == OrderItem.dish_id
        ).outerjoin(
            Order, sqlalchemy.and_(
                OrderItem.order_id == Order.id,
                Order.status == 'PAID'
            )
        ).filter(
            Dish.restaurant_id == restaurant.id
        ).group_by(Dish.id, Dish.name).all()
        
        total_value = sum(int(s[1]) for s in stats)
        total_label = '总份数'
    else:
        # 按销售额统计
        stats = extensions.db.session.query(
            Dish.name,
            sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.line_total), decimal.Decimal('0')).label('value')
        ).outerjoin(
            OrderItem, Dish.id == OrderItem.dish_id
        ).outerjoin(
            Order, sqlalchemy.and_(
                OrderItem.order_id == Order.id,
                Order.status == 'PAID'
            )
        ).filter(
            Dish.restaurant_id == restaurant.id
        ).group_by(Dish.id, Dish.name).all()
        
        total_value = sum(s[1] for s in stats) if stats else decimal.Decimal('0')
        total_label = '总消费额'
    
    # 检查是否有数据
    has_data = any(s[1] > 0 for s in stats) if stats else False
    
    return flask.render_template(
        'manager/reports.html',
        restaurant=restaurant,
        mode=mode,
        total_label=total_label,
        total_value=total_value,
        has_data=has_data
    )


@manager_bp.route('/reports/pie')
@flask_login.login_required
def pie_chart():
    """
    生成饼图图片
    返回PNG格式的图片
    只统计已支付(PAID)的订单
    """
    from app.manager.reports import generate_pie_chart
    
    # 验证餐厅所有权
    restaurant = _get_owner_restaurant()
    if not restaurant:
        flask.abort(403)
    
    # 获取报表模式
    mode = flask.request.args.get('mode', 'qty')
    if mode not in ('qty', 'amount'):
        mode = 'qty'
    
    # 查询各菜品的统计数据（只统计PAID订单）
    if mode == 'qty':
        # 按份数统计
        stats = extensions.db.session.query(
            Dish.name,
            sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.qty), 0).label('value')
        ).outerjoin(
            OrderItem, Dish.id == OrderItem.dish_id
        ).outerjoin(
            Order, sqlalchemy.and_(
                OrderItem.order_id == Order.id,
                Order.status == 'PAID'
            )
        ).filter(
            Dish.restaurant_id == restaurant.id
        ).group_by(Dish.id, Dish.name).all()
        
        data_dict = {s[0]: int(s[1]) for s in stats}
        total_value = sum(data_dict.values())
        title = f'{restaurant.name} - Portions'
        total_label = 'Total Portions'
    else:
        # 按销售额统计
        stats = extensions.db.session.query(
            Dish.name,
            sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.line_total), decimal.Decimal('0')).label('value')
        ).outerjoin(
            OrderItem, Dish.id == OrderItem.dish_id
        ).outerjoin(
            Order, sqlalchemy.and_(
                OrderItem.order_id == Order.id,
                Order.status == 'PAID'
            )
        ).filter(
            Dish.restaurant_id == restaurant.id
        ).group_by(Dish.id, Dish.name).all()
        
        data_dict = {s[0]: float(s[1]) for s in stats}
        total_value = f'{sum(data_dict.values()):.2f}'
        title = f'{restaurant.name} - Revenue'
        total_label = 'Total Revenue'
    
    # 生成饼图
    png_data = generate_pie_chart(data_dict, title, total_label, total_value)
    
    # 返回PNG图片
    response = flask.make_response(png_data)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


# ==================== 智能经营顾问（Step-5） ====================

@manager_bp.route('/advisor', methods=['GET', 'POST'])
@flask_login.login_required
def advisor():
    """
    经营顾问智能问答页面

    使用QA引擎回答关于餐厅经营的问题，支持：
    - 规则匹配的即时回答（常见分析问题）
    - LLM生成的智能建议
    - 基于真实数据的分析
    """
    import flask
    from flask import render_template, request, flash
    from flask_login import current_user
    from app.models import Restaurant
    from app.ai import deepseek_client
    from app.ai import qa_engine  # 新增导入

    # 获取当前用户的餐厅
    restaurant = Restaurant.query.filter_by(owner_user_id=current_user.id).first()
    if not restaurant:
        flash('您还没有创建餐厅', 'warning')
        return render_template('manager/advisor.html',
                               restaurant=None,
                               api_configured=False,
                               chat_history=[])

    # 检查API是否配置
    api_configured = deepseek_client.is_api_configured()

    # 获取聊天历史
    chat_history = get_advisor_chat_history()

    # 处理POST请求
    if request.method == 'POST' and api_configured:
        user_question = request.form.get('message', '').strip()

        if user_question:
            # 使用QA引擎回答问题
            answer, updated_history = qa_engine.answer_manager_question(
                current_user=current_user,
                restaurant_id=restaurant.id,
                question=user_question,
                chat_history=chat_history,
                model_override=None  # 使用默认模型，或设为 'deepseek-reasoner' 以获取更深入分析
            )

            # 保存更新后的历史
            save_advisor_chat_history(updated_history)
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
        'manager/advisor.html',
        restaurant=restaurant,
        api_configured=api_configured,
        chat_history=display_messages
    )


def _collect_business_data(restaurant):
    """
    收集餐厅经营数据用于AI分析
    只统计已支付(PAID)的订单
    
    参数:
        restaurant: 餐厅对象
        
    返回:
        dict: 包含各类经营数据的字典
    """
    data = {}
    
    # 1. 消费者排行（按总消费金额）
    top_consumers = extensions.db.session.query(
        User.id,
        User.username,
        sqlalchemy.func.sum(Order.total_amount).label('total_spend'),
        sqlalchemy.func.count(Order.id).label('order_count')
    ).join(
        Order, User.id == Order.user_id
    ).filter(
        Order.restaurant_id == restaurant.id,
        Order.status == 'PAID'
    ).group_by(User.id).order_by(
        sqlalchemy.desc('total_spend')
    ).limit(10).all()
    
    data['top_consumers'] = [
        {'user_id': c[0], 'username': c[1], 'total_spend': float(c[2]), 'order_count': c[3]}
        for c in top_consumers
    ]
    
    # 2. 菜品销量排行（按份数）
    dish_popularity = extensions.db.session.query(
        Dish.id,
        Dish.name,
        Dish.price,
        sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.qty), 0).label('total_qty')
    ).outerjoin(
        OrderItem, Dish.id == OrderItem.dish_id
    ).outerjoin(
        Order, sqlalchemy.and_(
            OrderItem.order_id == Order.id,
            Order.status == 'PAID'
        )
    ).filter(
        Dish.restaurant_id == restaurant.id
    ).group_by(Dish.id).order_by(
        sqlalchemy.desc('total_qty')
    ).all()
    
    data['dish_popularity'] = [
        {'dish_id': d[0], 'name': d[1], 'price': float(d[2]), 'total_qty': int(d[3])}
        for d in dish_popularity
    ]
    
    # 3. 菜品销售额排行
    dish_revenue = extensions.db.session.query(
        Dish.id,
        Dish.name,
        sqlalchemy.func.coalesce(sqlalchemy.func.sum(OrderItem.line_total), decimal.Decimal('0')).label('revenue')
    ).outerjoin(
        OrderItem, Dish.id == OrderItem.dish_id
    ).outerjoin(
        Order, sqlalchemy.and_(
            OrderItem.order_id == Order.id,
            Order.status == 'PAID'
        )
    ).filter(
        Dish.restaurant_id == restaurant.id
    ).group_by(Dish.id).order_by(
        sqlalchemy.desc('revenue')
    ).all()
    
    data['dish_revenue'] = [
        {'dish_id': d[0], 'name': d[1], 'revenue': float(d[2])}
        for d in dish_revenue
    ]
    
    # 4. 每个消费者最爱点的菜（Top 3）
    consumer_favorites = {}
    for consumer in top_consumers[:5]:  # 只统计前5名消费者
        favorites = extensions.db.session.query(
            Dish.name,
            sqlalchemy.func.sum(OrderItem.qty).label('qty')
        ).join(
            OrderItem, Dish.id == OrderItem.dish_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.restaurant_id == restaurant.id,
            Order.user_id == consumer[0],
            Order.status == 'PAID'
        ).group_by(Dish.id).order_by(
            sqlalchemy.desc('qty')
        ).limit(3).all()
        
        consumer_favorites[consumer[1]] = [
            {'name': f[0], 'qty': int(f[1])} for f in favorites
        ]
    
    data['consumer_favorites'] = consumer_favorites
    
    # 5. 总体统计
    total_stats = extensions.db.session.query(
        sqlalchemy.func.count(Order.id).label('order_count'),
        sqlalchemy.func.coalesce(sqlalchemy.func.sum(Order.total_amount), decimal.Decimal('0')).label('total_revenue')
    ).filter(
        Order.restaurant_id == restaurant.id,
        Order.status == 'PAID'
    ).first()
    
    data['total_stats'] = {
        'order_count': total_stats[0] if total_stats else 0,
        'total_revenue': float(total_stats[1]) if total_stats else 0
    }
    
    # 6. 消费者总数
    consumer_count = extensions.db.session.query(
        sqlalchemy.func.count(sqlalchemy.func.distinct(Order.user_id))
    ).filter(
        Order.restaurant_id == restaurant.id,
        Order.status == 'PAID'
    ).scalar()
    
    data['consumer_count'] = consumer_count or 0
    
    return data


def _build_advisor_system_prompt(restaurant, business_data):
    """
    构建经营顾问的系统提示词
    
    参数:
        restaurant: 餐厅对象
        business_data: 经营数据字典
        
    返回:
        str: 系统提示词
    """
    # 格式化消费者排行数据
    consumers_text = ""
    if business_data['top_consumers']:
        consumers_text = "消费者排行（按总消费金额）：\n"
        for i, c in enumerate(business_data['top_consumers'], 1):
            consumers_text += f"  {i}. {c['username']}（ID:{c['user_id']}）- 消费 ¥{c['total_spend']:.2f}，共 {c['order_count']} 单\n"
    else:
        consumers_text = "消费者排行：暂无数据\n"
    
    # 格式化菜品销量排行
    popularity_text = ""
    if business_data['dish_popularity']:
        popularity_text = "菜品销量排行（按份数）：\n"
        for i, d in enumerate(business_data['dish_popularity'], 1):
            popularity_text += f"  {i}. {d['name']}（¥{d['price']:.2f}）- 售出 {d['total_qty']} 份\n"
    else:
        popularity_text = "菜品销量排行：暂无数据\n"
    
    # 格式化菜品销售额排行
    revenue_text = ""
    if business_data['dish_revenue']:
        revenue_text = "菜品销售额排行：\n"
        for i, d in enumerate(business_data['dish_revenue'], 1):
            revenue_text += f"  {i}. {d['name']} - 销售额 ¥{d['revenue']:.2f}\n"
    else:
        revenue_text = "菜品销售额排行：暂无数据\n"
    
    # 格式化消费者最爱菜品
    favorites_text = ""
    if business_data['consumer_favorites']:
        favorites_text = "主要消费者最爱点的菜：\n"
        for username, favs in business_data['consumer_favorites'].items():
            if favs:
                fav_list = "、".join([f"{f['name']}({f['qty']}份)" for f in favs])
                favorites_text += f"  {username}：{fav_list}\n"
    else:
        favorites_text = "消费者最爱菜品：暂无数据\n"
    
    # 总体统计
    total_stats = business_data['total_stats']
    stats_text = f"""总体统计：
  - 总订单数：{total_stats['order_count']} 单
  - 总营业额：¥{total_stats['total_revenue']:.2f}
  - 消费者总数：{business_data['consumer_count']} 人
"""
    
    system_prompt = f"""你是「{restaurant.name}」餐厅的智能经营分析顾问。你的任务是根据提供的经营数据回答老板的问题，并给出专业的经营建议。

【当前经营数据】

{stats_text}
{consumers_text}
{popularity_text}
{revenue_text}
{favorites_text}

【回答规则】
1. 请用中文回答所有问题
2. 只能基于上面提供的数据进行分析和回答
3. 如果数据不足以回答某个问题，请明确说明"根据现有数据无法确认"
4. 回答要专业、有条理，适当使用要点列表
5. 可以给出合理的经营建议和分析
6. 不要编造数据中不存在的信息
7. 金额使用人民币（¥），保留两位小数

请开始为餐厅老板提供经营分析服务！"""
    
    return system_prompt
