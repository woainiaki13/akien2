# 🍽️ 餐厅订餐系统 - 项目交接文档

> 本文档供接手开发的同学参考，包含项目架构、安装步骤、已知问题等信息。

---

## 📋 项目概述

本项目是一个基于 Flask 的网络餐厅订餐平台，包含：

- **用户系统**: 注册/登录/头像上传
- **餐厅管理**: 创建餐厅、菜品管理、黑名单
- **订餐系统**: 餐厅列表、菜单浏览、购物车、结算
- **数据分析**: 菜品统计、消费者分析、饼图报表
- **智能问答**: 菜品咨询、经营顾问（DeepSeek AI）

---

## 🏗️ 项目架构

### 目录结构

```
flask_restaurant_app/
├── app/
│   ├── __init__.py          # 应用工厂函数
│   ├── config.py             # 配置类
│   ├── constants.py          # 常量定义（分类、UI文本）
│   ├── extensions.py         # Flask扩展初始化
│   ├── models.py             # 数据库模型
│   ├── ai/                   # AI模块（Step-5）
│   │   ├── __init__.py
│   │   └── deepseek_client.py
│   ├── auth/                 # 认证蓝图（Step-1）
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── main/                 # 主蓝图
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── manager/              # 管理蓝图（Step-2/3/4/5）
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── reports.py        # 饼图生成（Step-4）
│   │   └── routes.py
│   ├── order/                # 订餐蓝图（Step-3/5）
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/            # HTML模板
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── main/
│   │   ├── manager/
│   │   └── order/
│   ├── static/               # 静态文件
│   │   └── uploads/
│   └── utils/                # 工具函数
│       └── images.py
├── migrations/               # 数据库迁移文件
├── requirements.txt          # Python依赖
├── run.py                    # 启动入口
├── .env                      # 环境变量（不要提交）
└── README*.md                # 文档
```

### 蓝图说明

| 蓝图 | URL前缀 | 功能 |
|------|---------|------|
| `auth_bp` | `/auth` | 用户认证（登录/注册/登出） |
| `main_bp` | `/` | 首页、选择页、入口路由 |
| `manager_bp` | `/manager` | 餐厅管理、数据分析、顾问 |
| `order_bp` | `/order` | 订餐、购物车、结算、问答 |

### 数据模型

```
User (用户)
  ├── Restaurant (餐厅) [一对一]
  ├── Order (订单) [一对多]
  └── Blacklist (黑名单记录) [一对多]

Restaurant (餐厅)
  ├── Category (分类) [一对多，固定4个]
  ├── Dish (菜品) [一对多]
  ├── Order (订单) [一对多]
  └── Blacklist (黑名单记录) [一对多]

Order (订单)
  └── OrderItem (订单项) [一对多]

Dish (菜品)
  └── OrderItem (订单项) [一对多]
```

---

## 🚀 环境搭建

> 重要：项目的最终操作规则以 `CONTRACT.md` 为准（若与本文冲突，以 CONTRACT.md 为准）。

### 1. 克隆/解压项目

确保项目根目录下存在 `run.py`、`requirements.txt`、`migrations/`。

### 2. 创建虚拟环境（建议）

```bash
python -m venv venv
```

Windows PowerShell 进入虚拟环境：

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. 安装依赖（Windows 推荐写法）

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

> 不建议直接敲 `pip install ...` 或 `flask ...`，避免误用到 Anaconda / 全局 Python。

### 4. 配置环境变量

创建 `.env` 文件（不要提交到仓库）：

```env
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1

# DeepSeek（Step-5）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_MODEL=deepseek-chat
# DEEPSEEK_TIMEOUT_SECONDS=30
```

### 5. 升级数据库（必须）

```powershell
.\venv\Scripts\python.exe -m flask --app run.py db upgrade
```

> 若出现 `no such table: restaurants`，请按下面顺序排查：  
> 1) 先确认你在项目根目录（能看到 `run.py`）执行命令；  
> 2) 确认 `migrations/versions/` 目录下存在创建 `restaurants/categories/dishes/orders/...` 的迁移脚本（拉取/覆盖到最新代码后再试）；  
> 3) 重新执行一次：`venv\Scripts\python.exe -m flask --app run.py db upgrade`；  
> 4) 如果你不需要保留本地数据，直接删除根目录的 `app.db` 后再执行 `db upgrade`（会自动重新建表）。

### 6. 启动应用（Windows PowerShell 标准命令）

```powershell
.\venv\Scripts\python.exe -m flask --app run.py run --debug
```

默认数据库为项目根目录下的 `app.db`（也可通过 `DATABASE_URL` 覆盖）。

---

## 📜 迁移时间线

| Step | 迁移内容 | 说明 |
|------|----------|------|
| Step-1 | User 模型 | 用户表 |
| Step-2 | Restaurant, Category, Dish, Order, OrderItem | 餐厅、分类、菜品、订单 |
| Step-3 | Blacklist | 黑名单表 |
| Step-4 | 无 | 仅新增路由和模板 |
| Step-5 | 无 | 仅新增AI功能 |

---

## 🔗 路由清单

### 认证 (`/auth`)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET/POST | `/auth/register` | 用户注册 |
| GET/POST | `/auth/login` | 用户登录 |
| GET | `/auth/logout` | 用户登出 |

### 主页 (`/`)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/` | 首页 |
| GET | `/choice` | 选择页（管理/订餐） |
| GET | `/manage` | 重定向到管理首页 |
| GET | `/order` | 重定向到订餐首页 |

### 管理 (`/manager`)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/manager/` | 管理首页/仪表盘 |
| GET/POST | `/manager/create-restaurant` | 创建餐厅 |
| GET/POST | `/manager/add-dish/<category>` | 添加菜品 |
| POST | `/manager/delete-dish/<id>` | 删除菜品 |
| GET | `/manager/blacklist` | 黑名单管理 |
| POST | `/manager/blacklist/add` | 添加黑名单 |
| POST | `/manager/blacklist/remove/<id>` | 移除黑名单 |
| GET | `/manager/stats/dishes` | 菜品统计 |
| GET | `/manager/consumers` | 消费者列表 |
| GET | `/manager/consumers/<id>/history` | 消费者详情 |
| GET | `/manager/reports` | 菜品报表 |
| GET | `/manager/reports/pie` | 饼图图片 |
| GET/POST | `/manager/advisor` | 经营顾问 |

### 订餐 (`/order`)
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/order/` | 餐厅列表 |
| GET | `/order/restaurant/<id>` | 餐厅菜单 |
| GET | `/order/dish/<id>` | 菜品详情 |
| POST | `/order/cart/add/<id>` | 添加到购物车 |
| POST | `/order/cart/set/<id>` | 设置数量 |
| POST | `/order/cart/clear` | 清空购物车 |
| GET | `/order/cart` | 查看购物车 |
| POST | `/order/checkout` | 结算付款 |
| GET/POST | `/order/ask/<id>` | 菜品问答 |

---

## ⚠️ 已知问题与解决方案

### 1. requirements.txt 编码问题（Windows）

**问题**: pip 安装时报 GBK 解码错误

**原因**: requirements.txt 包含非 ASCII 字符或编码不正确

**解决**: 
- 确保文件为 UTF-8 编码
- 不要在 requirements.txt 中写中文注释
- 中文说明写在 README 中

### 2. Flask 应用上下文错误

**问题**: "Working outside of application context"

**原因**: 在 app factory 阶段访问 `db.engine`

**解决**: 
- 使用 `sqlalchemy.engine.Engine` 监听器
- 在 `app/extensions.py` 中正确设置

```python
import sqlalchemy

@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

### 3. app.extensions 命名冲突

**问题**: AttributeError: 'dict' object has no attribute 'db'

**原因**: 混淆 Flask 的 `app.extensions`（dict）与项目模块

**解决**: 使用别名导入

```python
import app.extensions as extensions
extensions.db  # 正确
```

### 4. 常量导入错误

**问题**: ImportError: cannot import name 'FIXED_CATEGORIES'

**原因**: 名称不一致或拼写错误

**解决**: 使用模块导入

```python
import app.constants as constants
constants.FIXED_CATEGORIES  # 正确
```

### 5. Session Cookie 过大

**问题**: 聊天历史导致 Session 过大

**解决**: 已限制聊天历史最多 10 轮（MAX_CHAT_TURNS）

---

## 📝 开发规范

根据 `CONTRACT.md` 规定：

1. **变量/函数/类/文件名**: 必须使用英文
2. **代码注释**: 必须使用中文
3. **库函数调用**: 必须使用 `module.function()` 形式
4. **用户界面文本**: 必须使用中文
5. **文件编码**: .py/.html/.md 必须使用 UTF-8
6. **requirements.txt**: 必须 ASCII 安全，无中文注释

### 示例

```python
# -*- coding: utf-8 -*-
"""
模块说明（中文）
"""

import flask
import flask_login

# 这是中文注释
def get_user_restaurant():
    """获取当前用户的餐厅（中文docstring）"""
    return flask.redirect(flask.url_for('manager.home'))
```

---

## 🧪 测试清单

- [ ] 用户注册/登录/登出
- [ ] 头像上传（<= 100x100）
- [ ] 创建餐厅
- [ ] 添加/删除菜品
- [ ] 餐厅列表（按销售额排序）
- [ ] 浏览菜单/菜品详情
- [ ] 购物车（添加/修改数量/清空）
- [ ] 结算付款
- [ ] 黑名单（添加/移除/拦截）
- [ ] 菜品统计
- [ ] 消费者列表/详情
- [ ] 饼图报表（份数/销售额）
- [ ] 菜品问答（需 API Key）
- [ ] 经营顾问（需 API Key）

---

## 📞 联系方式

如有问题，请参考各 Step 的 README 文档，或查看 `CONTRACT.md` 合同文件。

---

*最后更新: Step-5 完成*
