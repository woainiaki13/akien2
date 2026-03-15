"""创建核心业务表

Revision ID: 78c7fc923567
Revises: 2830ad1a65cf
Create Date: 2026-01-10

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78c7fc923567'
down_revision = '2830ad1a65cf'
branch_labels = None
depends_on = None


def upgrade():
    """创建餐厅订餐平台的核心业务表。"""

    # restaurants
    op.create_table(
        'restaurants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('logo_path', sa.String(length=256), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_restaurants_name'),
        sa.UniqueConstraint('owner_user_id', name='uq_restaurants_owner_user_id'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_restaurants_name', 'restaurants', ['name'], unique=True)

    # categories
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('restaurant_id', 'name', name='uq_restaurant_category'),
    )
    op.create_index('ix_categories_restaurant_id', 'categories', ['restaurant_id'], unique=False)

    # dishes
    op.create_table(
        'dishes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_path', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_dishes_restaurant_id', 'dishes', ['restaurant_id'], unique=False)
    op.create_index('ix_dishes_category_id', 'dishes', ['category_id'], unique=False)

    # orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PAID'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_orders_restaurant_id', 'orders', ['restaurant_id'], unique=False)
    op.create_index('ix_orders_user_id', 'orders', ['user_id'], unique=False)
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)

    # order_items
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('dish_id', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'], unique=False)
    op.create_index('ix_order_items_dish_id', 'order_items', ['dish_id'], unique=False)

    # blacklist
    op.create_table(
        'blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('restaurant_id', 'user_id', name='uq_restaurant_user_blacklist'),
    )
    op.create_index('ix_blacklist_restaurant_id', 'blacklist', ['restaurant_id'], unique=False)
    op.create_index('ix_blacklist_user_id', 'blacklist', ['user_id'], unique=False)


def downgrade():
    """回滚本次创建的核心业务表。"""
    op.drop_index('ix_blacklist_user_id', table_name='blacklist')
    op.drop_index('ix_blacklist_restaurant_id', table_name='blacklist')
    op.drop_table('blacklist')

    op.drop_index('ix_order_items_dish_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')

    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_index('ix_orders_restaurant_id', table_name='orders')
    op.drop_table('orders')

    op.drop_index('ix_dishes_category_id', table_name='dishes')
    op.drop_index('ix_dishes_restaurant_id', table_name='dishes')
    op.drop_table('dishes')

    op.drop_index('ix_categories_restaurant_id', table_name='categories')
    op.drop_table('categories')

    op.drop_index('ix_restaurants_name', table_name='restaurants')
    op.drop_table('restaurants')
