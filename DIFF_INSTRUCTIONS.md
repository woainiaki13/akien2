# QA引擎集成 - 修改说明文档

本文档详细说明如何将QA引擎集成到现有的Flask餐厅平台中。

## 一、修改概览

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `app/ai/__init__.py` | 修改 | 添加新模块导入 |
| `app/order/routes.py` | 修改 | 使用qa_engine回答菜品问题 |
| `app/manager/routes.py` | 修改 | 使用qa_engine回答经营问题 |
| `app/ai/qa_engine.py` | 新增 | QA引擎核心模块 |
| `app/ai/qa_prompts.py` | 新增 | 系统提示词模块 |
| `app/ai/qa_matcher.py` | 新增 | 菜品名称匹配模块 |

---

## 二、详细DIFF

### 2.1 修改 `app/ai/__init__.py`

```diff
--- a/app/ai/__init__.py
+++ b/app/ai/__init__.py
@@ -1,5 +1,8 @@
 # -*- coding: utf-8 -*-
 """
 AI模块初始化
 """
 from app.ai import deepseek_client
+from app.ai import qa_engine
+from app.ai import qa_prompts
+from app.ai import qa_matcher
```

### 2.2 修改 `app/order/routes.py`

找到原有的 `ask` 函数（大约在第487-564行），进行以下修改：

```diff
--- a/app/order/routes.py
+++ b/app/order/routes.py
@@ -1,6 +1,7 @@
 # 在文件顶部的 import 区域添加
 from app.ai import deepseek_client
+from app.ai import qa_engine
 
 # ... 其他代码 ...
 
@@ -487,50 +488,35 @@ def ask(dish_id):
     """
-    菜品智能问答页面
+    菜品智能问答页面 - 使用QA引擎
     """
     dish = Dish.query.get_or_404(dish_id)
     api_configured = deepseek_client.is_api_configured()
     
     chat_key = f"dish:{dish_id}"
     chat_history = get_ai_chat_history(chat_key)
     
     if request.method == 'POST' and api_configured:
         user_question = request.form.get('question', '').strip()
         
         if user_question:
-            # 原有代码：直接调用 deepseek_client
-            # system_prompt = _build_dish_system_prompt(dish, restaurant)
-            # messages = [{"role": "system", "content": system_prompt}]
-            # messages.extend(chat_history)
-            # messages.append({"role": "user", "content": user_question})
-            # try:
-            #     response = deepseek_client.call_chat_completion(messages, ...)
-            #     ...
-            # except Exception as e:
-            #     ...
-            
-            # 新代码：使用 qa_engine
+            # 使用QA引擎回答问题
             answer, updated_history = qa_engine.answer_dish_question(
                 current_user=current_user,
                 dish_id=dish_id,
                 question=user_question,
-                chat_history=chat_history
+                chat_history=chat_history,
+                model_override=None
             )
             
             save_ai_chat_history(chat_key, updated_history)
             chat_history = updated_history
-            
-            # 移除原有的 _build_dish_system_prompt 和相关处理
     
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
```

**可删除的原有函数**（如果存在的话）：
- `_build_dish_system_prompt()` - 已被 `qa_prompts.get_dish_system_prompt()` 替代

### 2.3 修改 `app/manager/routes.py`

找到原有的 `advisor` 函数（大约在第743-826行），进行以下修改：

```diff
--- a/app/manager/routes.py
+++ b/app/manager/routes.py
@@ -1,6 +1,7 @@
 # 在文件顶部的 import 区域添加
 from app.ai import deepseek_client
+from app.ai import qa_engine
 
 # ... 其他代码 ...
 
@@ -743,60 +744,40 @@ def advisor():
     """
-    经营顾问智能问答页面
+    经营顾问智能问答页面 - 使用QA引擎
     """
     restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
     if not restaurant:
         flash('您还没有创建餐厅', 'warning')
         return render_template('manager/advisor.html', 
                              restaurant=None, 
                              api_configured=False,
                              chat_history=[])
     
     api_configured = deepseek_client.is_api_configured()
     chat_history = get_advisor_chat_history()
     
     if request.method == 'POST' and api_configured:
         user_question = request.form.get('question', '').strip()
         
         if user_question:
-            # 原有代码：直接调用 deepseek_client
-            # business_data = _collect_business_data(restaurant)
-            # system_prompt = _build_advisor_system_prompt()
-            # ...
-            
-            # 新代码：使用 qa_engine
+            # 使用QA引擎回答问题
             answer, updated_history = qa_engine.answer_manager_question(
                 current_user=current_user,
                 restaurant_id=restaurant.id,
                 question=user_question,
-                chat_history=chat_history
+                chat_history=chat_history,
+                model_override=None  # 可设为 'deepseek-reasoner'
             )
             
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
```

**可删除的原有函数**（如果存在的话）：
- `_collect_business_data()` - 已被 `qa_engine.build_restaurant_snapshot()` 替代
- `_build_advisor_system_prompt()` - 已被 `qa_prompts.get_manager_system_prompt()` 替代

---

## 三、数据查询说明

所有统计查询都遵循 `Order.status == "PAID"` 的约束：

### 3.1 顶级消费者查询
```python
db.session.query(
    User.id, User.username, User.avatar,
    func.sum(Order.total_amount).label('total_spent'),
    func.count(Order.id).label('order_count')
).join(Order, Order.user_id == User.id).filter(
    Order.restaurant_id == restaurant_id,
    Order.status == 'PAID'  # 关键过滤条件
).group_by(User.id).order_by(desc('total_spent'))
```

### 3.2 菜品销量查询
```python
db.session.query(
    Dish.name,
    func.sum(OrderItem.quantity).label('total_qty')
).join(OrderItem, Dish.id == OrderItem.dish_id
).join(Order, OrderItem.order_id == Order.id).filter(
    Order.restaurant_id == restaurant_id,
    Order.status == 'PAID'  # 关键过滤条件
).group_by(Dish.id).order_by(desc('total_qty'))
```

### 3.3 菜品购买者查询
```python
db.session.query(
    User.username,
    func.sum(OrderItem.quantity).label('qty')
).join(Order, Order.user_id == User.id
).join(OrderItem, OrderItem.order_id == Order.id).filter(
    OrderItem.dish_id == dish_id,
    Order.status == 'PAID'  # 关键过滤条件
).group_by(User.id)
```

---

## 四、规则匹配模式

### 4.1 经营顾问规则

| 模式 | 匹配关键词 | 直接查询 |
|------|-----------|----------|
| VIP客户 | `vip`, `消费最多`, `顶级客户` | 消费金额Top5 |
| 畅销菜品 | `卖得最好`, `销量冠军`, `最受欢迎` | 销量Top5 |
| 总营收 | `总营收`, `总收入`, `赚了多少` | SUM(total_amount) |
| 订单数 | `多少订单`, `订单量` | COUNT(orders) |
| 收入排行 | `哪个菜赚钱`, `收入排行` | 按收入Top5 |

### 4.2 菜品问答规则

| 模式 | 匹配关键词 | 直接查询 |
|------|-----------|----------|
| 价格 | `多少钱`, `价格`, `几元` | dish.price |
| 销量 | `销量`, `卖了多少` | SUM(quantity) |
| 购买者 | `谁点过`, `谁买过` | DISTINCT users |
| 介绍 | `介绍`, `是什么` | dish.description |

---

## 五、聊天历史管理

- **存储位置**: `flask.session['ai_chat']`
- **最大轮数**: 10轮（20条消息）
- **自动修剪**: 超过限制时保留最近的消息
- **Session结构**:
  ```python
  {
      'ai_chat': {
          'order': {
              'dish:123': [...],  # 菜品问答历史
              'dish:456': [...]
          },
          'manager': {
              'advisor': [...]    # 经营顾问历史
          }
      }
  }
  ```

---

## 六、错误处理

QA引擎统一处理以下错误情况：

1. **API未配置**: 返回 "智能问答功能未配置，请联系管理员设置 DEEPSEEK_API_KEY。"
2. **网络超时**: 返回 deepseek_client 的友好错误消息
3. **菜品不存在**: 返回 "抱歉，找不到该菜品信息。"
4. **餐厅不存在**: 快照返回 `{"error": "餐厅不存在"}`

---

## 七、模型选择（可选功能）

通过 `model_override` 参数可以为不同场景指定不同模型：

```python
# 菜品问答 - 使用快速响应模型
answer, history = qa_engine.answer_dish_question(
    ...,
    model_override='deepseek-chat'
)

# 经营顾问 - 使用推理增强模型
answer, history = qa_engine.answer_manager_question(
    ...,
    model_override='deepseek-reasoner'
)
```

如果不指定，则使用环境变量 `DEEPSEEK_MODEL` 的值（默认 `deepseek-chat`）。
