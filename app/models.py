# -*- coding: utf-8 -*-
"""
数据库模型定义模块
"""

import datetime

import flask_login
import werkzeug.security

import app.extensions as extensions


db = extensions.db


class User(flask_login.UserMixin, db.Model):
    """
    用户模型类
    继承UserMixin以支持Flask-Login的用户会话管理
    """
    __tablename__ = 'users'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 用户名，唯一且不能为空
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # 邮箱，唯一且不能为空
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # 密码哈希值，不能为空
    password_hash = db.Column(db.String(256), nullable=False)
    
    # 头像路径，存储相对路径如 "uploads/avatars/xxx.jpg"
    avatar_path = db.Column(db.String(256), nullable=False)
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 关系：用户拥有的餐厅（一对一）
    restaurant = db.relationship('Restaurant', backref='owner', uselist=False, cascade='all, delete-orphan')
    
    # 关系：用户的订单
    orders = db.relationship('Order', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    
    # 关系：用户被拉黑的记录
    blacklist_entries = db.relationship('Blacklist', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """
        设置用户密码
        使用werkzeug的密码哈希函数加密存储
        
        参数:
            password: 明文密码
        """
        self.password_hash = werkzeug.security.generate_password_hash(password)
    
    def check_password(self, password):
        """
        验证用户密码
        
        参数:
            password: 待验证的明文密码
            
        返回:
            bool: 密码是否正确
        """
        return werkzeug.security.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        """返回用户对象的字符串表示"""
        return f'<User {self.username}>'


class Restaurant(db.Model):
    """
    餐厅模型类
    每个用户只能拥有一个餐厅
    """
    __tablename__ = 'restaurants'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 餐厅名称，全局唯一
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Logo路径
    logo_path = db.Column(db.String(256), nullable=False)
    
    # 所有者用户ID，外键关联到User表
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 关系：餐厅的类别
    categories = db.relationship('Category', backref='restaurant', lazy='dynamic', 
                                cascade='all, delete-orphan')
    
    # 关系：餐厅的菜品
    dishes = db.relationship('Dish', backref='restaurant', lazy='dynamic',
                            cascade='all, delete-orphan')
    
    # 关系：餐厅的订单
    orders = db.relationship('Order', backref='restaurant', lazy='dynamic',
                            cascade='all, delete-orphan')
    
    # 关系：餐厅的黑名单
    blacklist = db.relationship('Blacklist', backref='restaurant', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        """返回餐厅对象的字符串表示"""
        return f'<Restaurant {self.name}>'


class Category(db.Model):
    """
    类别模型类
    每个餐厅有固定的4个类别：Drink, Dish, Staple, Other
    """
    __tablename__ = 'categories'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 所属餐厅ID
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'), 
                             nullable=False)
    
    # 类别名称（英文：Drink, Dish, Staple, Other）
    name = db.Column(db.String(50), nullable=False)
    
    # 唯一约束：同一餐厅下类别名称唯一
    __table_args__ = (
        db.UniqueConstraint('restaurant_id', 'name', name='uq_restaurant_category'),
    )
    
    # 关系：类别下的菜品
    dishes = db.relationship('Dish', backref='category', lazy='dynamic',
                            cascade='all, delete-orphan')
    
    def __repr__(self):
        """返回类别对象的字符串表示"""
        return f'<Category {self.name}>'


class Dish(db.Model):
    """
    菜品模型类
    """
    __tablename__ = 'dishes'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 所属餐厅ID
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'), 
                             nullable=False)
    
    # 所属类别ID
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), 
                           nullable=False)
    
    # 菜品名称
    name = db.Column(db.String(100), nullable=False)
    
    # 价格（精确到分）
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # 描述
    description = db.Column(db.Text, nullable=False)
    
    # 图片路径
    image_path = db.Column(db.String(256), nullable=False)
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 关系：菜品的订单项
    order_items = db.relationship('OrderItem', backref='dish', lazy='dynamic',
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        """返回菜品对象的字符串表示"""
        return f'<Dish {self.name}>'


class Order(db.Model):
    """
    订单模型类
    记录用户在餐厅的订单
    """
    __tablename__ = 'orders'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 所属餐厅ID
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'), 
                             nullable=False)
    
    # 下单用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                       nullable=False)
    
    # 订单总金额
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # 订单状态（DRAFT:草稿, PAID:已支付, COMPLETED:已完成, CANCELLED:已取消）
    status = db.Column(db.String(20), nullable=False, default='PAID')
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 关系：订单的订单项
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic',
                                 cascade='all, delete-orphan')
    
    def __repr__(self):
        """返回订单对象的字符串表示"""
        return f'<Order {self.id}>'


class OrderItem(db.Model):
    """
    订单项模型类
    记录订单中的具体菜品及数量
    """
    __tablename__ = 'order_items'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 所属订单ID
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), 
                        nullable=False)
    
    # 菜品ID（级联删除：删除菜品时自动删除相关订单项）
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id', ondelete='CASCADE'), 
                       nullable=False)
    
    # 数量
    qty = db.Column(db.Integer, nullable=False)
    
    # 单价（快照，记录下单时的价格）
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # 小计
    line_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        """返回订单项对象的字符串表示"""
        return f'<OrderItem {self.id}>'


class Blacklist(db.Model):
    """
    黑名单模型类
    记录被餐厅拉黑的用户
    """
    __tablename__ = 'blacklist'
    
    # 主键ID
    id = db.Column(db.Integer, primary_key=True)
    
    # 餐厅ID（级联删除：删除餐厅时自动删除黑名单记录）
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'), 
                             nullable=False)
    
    # 用户ID（级联删除：删除用户时自动删除黑名单记录）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                       nullable=False)
    
    # 创建时间（拉黑时间）
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # 唯一约束：同一餐厅下同一用户只能有一条黑名单记录
    __table_args__ = (
        db.UniqueConstraint('restaurant_id', 'user_id', name='uq_restaurant_user_blacklist'),
    )
    
    def __repr__(self):
        """返回黑名单对象的字符串表示"""
        return f'<Blacklist restaurant={self.restaurant_id} user={self.user_id}>'
