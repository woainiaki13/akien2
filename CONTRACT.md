# CONTRACT.md（Team Debug & Rewrite Contract / Up to Step-5）

目的：确保任何组员都能稳定地用 AI（Claude/ChatGPT）对本项目进行 Debug 与文件改写，并且不破坏现有功能。

优先级：本文件 > 其它 README/聊天记录。冲突时以本文件为准。

---

## 1. 项目概览（当前已完成到 Step-5）

本项目为 Flask 餐厅订餐平台，已具备：认证、管理端、点餐端、统计分析、DeepSeek 智能问答。目录与模块结构以交接文档为准。

核心模块：

- `app/auth`：注册/登录/头像上传
- `app/main`：入口/choice 页；`/manage`、`/order` 重定向入口
- `app/manager`：餐厅管理、黑名单、统计分析、经营顾问
- `app/order`：订餐、购物车、结算、菜品问答
- `app/ai`：DeepSeek client 封装（requests 调用）

依赖清单：`requirements.txt` 必须包含 Flask、Flask-SQLAlchemy、Flask-Migrate、requests、matplotlib 等。

---

## 2. 硬性编码规范（Non-negotiables）

AI 改代码必须严格遵守，否则视为“不合格交付”。

1. **变量名/函数名/类名/文件名：全部英文**
2. **代码注释：全部中文（docstring 也建议中文）**
3. **库函数调用必须写成 `module.function()`**
   - 例如：`flask.render_template()`、`sqlalchemy.func.sum()`、`requests.post()`
   - 强烈建议：`import module`，尽量避免 `from x import y`
4. **所有用户可见 UI 文案必须中文**
   - 标题、按钮、表单 label、placeholder、flash、验证错误、空状态、报错提示
5. **编码要求**
   - `.py` / `.html` / `.md` 必须 UTF-8
   - `requirements.txt` 必须 ASCII-safe UTF-8，禁止中文注释（Windows pip GBK 解码会炸）

---

## 3. 业务“真相规则”（不要被 AI 改坏）

### 3.1 固定分类（永不变）

- 内部值：`Drink / Dish / Staple / Other`
- UI 中文：`饮品 / 菜品 / 主食 / 其他`
- 来源：`app/constants.py`（建议模块导入 `import app.constants as constants`，减少 ImportError）

### 3.2 统计口径（强约束）

- 所有统计/排行/报表只统计：`Order.status == "PAID"`

### 3.3 黑名单拦截（强约束）

- 黑名单用户：
  - 进入餐厅时必须提示已被拉黑
  - 加入购物车必须拦截
  - 结算必须再次拦截

### 3.4 删除菜品级联删除（强约束）

- 删除 Dish 后，与之相关 OrderItem 必须删除（FK cascade）
- 若出现残留数据需检查 SQLite `foreign_keys` 是否开启

---

## 4. 环境与启动（Windows 重点：避免 Anaconda/venv 混用）

### 4.1 统一要求

- 必须在项目根目录运行（包含 `run.py`）
- 建议永远使用 venv 的 python 启动和迁移，不要直接敲 `flask`（防止走到 Anaconda 的 Flask）

### 4.2 Windows PowerShell 标准命令（组内统一）

```powershell
# 1) 安装依赖（必须）
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 升级数据库（必须：restaurants 等表来自迁移）
.\venv\Scripts\python.exe -m flask --app run.py db upgrade

# 3) 启动
.\venv\Scripts\python.exe -m flask --app run.py run --debug
```

`config` 默认数据库为项目根目录的 `app.db`，也可被 `DATABASE_URL` 覆盖。

若出现 `no such table: restaurants`，基本就是没执行 `db upgrade` 或连错数据库。

---

## 5. DeepSeek 智能问答（Step-5）契约

- 点餐端：`/order/ask/<dish_id>` 菜品问答（真实调用 DeepSeek，不是占位）
- 管理端：`/manager/advisor` 经营顾问（真实调用 DeepSeek）
- 必需环境变量：`DEEPSEEK_API_KEY`
- 可选：
  - `DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com`）
  - `DEEPSEEK_MODEL`（默认 `deepseek-chat`）
  - `DEEPSEEK_TIMEOUT_SECONDS`（默认 `30`）

若 API Key 未配置：

- 页面必须显示中文提示 **“智能问答功能未配置”**
- 表单禁用/不崩溃

---

## 6. 已知高频故障（AI Debug 必须先对照这里）

以下问题在历史中真实出现过，AI 修复必须避免“回归”：

1. `requirements.txt` 编码/中文注释导致 Windows pip GBK 解码失败
   - 解决：`requirements.txt` 只写依赖行，不写中文；中文写 README
2. `Working outside of application context`
   - 根因：在 app factory/import 阶段访问 `db.engine` 做 event listen
   - 解决：监听 `sqlalchemy.engine.Engine`，仅对 `sqlite3.Connection` 执行 `PRAGMA foreign_keys=ON`
3. `app.extensions` 命名冲突
   - Flask 的 `app.extensions` 是 dict
   - 解决：`import app.extensions as extensions` 后用 `extensions.db` 等
4. `constants` 常量名不一致导致 ImportError（如 `FIXED_CATEGORIES`）
   - 解决：优先模块导入 `import app.constants as constants`，避免 `from ... import ...` 的脆弱导入
5. `requests` 模块缺失
   - 根因：依赖没装或运行环境不是 venv
   - 解决：用 venv 的 python 执行 pip install；requirements 已包含 requests

---

## 7. AI Debug/改文件的“标准交付流程”（组内强制）

当你让 AI 修 bug 或改功能，必须在 prompt 里要求 AI：

### 7.1 必须输出

1. 定位原因：指明报错的根因（引用 traceback 行）
2. 最小修复方案：优先少改动、可回滚
3. 修改文件清单：哪些文件改了、为什么
4. 迁移/依赖影响：是否需要 pip install 或 flask db upgrade
5. 验证步骤：给出可复制的命令与浏览器测试路径

### 7.2 打包规则（强制）

- AI 必须分别打包：
  - `modified_existing_files_*.zip`：仅包含修改过的旧文件
  - `new_files_*.zip`：仅包含新增文件
- 同时输出 manifest（每个 zip 的文件列表 + 1 句修改原因）

---

## 8. 组员给 AI 的 Prompt 模板（建议复制使用）

每次 debug 都用这个模板开新对话，避免上下文丢失。

```text
You are a senior Flask full-stack engineer. Debug and patch the project.

You MUST follow CONTRACT.md:
- English identifiers, Chinese comments
- module.function() calls (prefer import module)
- all UI Chinese, UTF-8 files
- requirements.txt ASCII-safe UTF-8 no Chinese comments
- stats only count Order.status == "PAID"
- blacklist enforcement must not regress

INPUTS:
1) Error traceback: <paste>
2) Current OS: Windows PowerShell
3) How I start the app: .\venv\Scripts\python.exe -m flask --app run.py run --debug
4) What I ran before the error (pip/migrations): <paste>

TASK:
- Find root cause
- Propose minimal fix
- Provide exact code diffs for changed files
- Provide exact commands to verify
- Package output into:
  - modified_existing_files_fix.zip
  - new_files_fix.zip
- Print manifest for both zips
```

---

## 9. 交付给同学的“最终说明文件”要求

项目交接说明以 `PROJECT_HANDOFF_zh.md` 为准（已包含结构/路由/已知问题/规范/测试清单）。

Step-5 运行与 DeepSeek 配置以 `README_step5_zh.md` 为准。

Step-5 文件清单与集成步骤以 `MANIFEST_step5.md` 为准。

---

## 10. 必须通过的回归测试清单（每次修复都要跑）

- 注册/登录/登出正常
- 头像上传限制正常
- 创建餐厅 + 固定 4 分类存在
- 添加菜品/删除菜品正常（删除无残留 OrderItem）
- 订餐：餐厅按销售额排序；菜单/详情/购物车/结算落库
- 黑名单：进入/加购/结算均拦截
- Step-4：菜品统计/消费者列表/消费者历史/饼图正常；统计仅 PAID
- Step-5：菜品问答与经营顾问可用；API Key 缺失时中文提示且不崩溃
