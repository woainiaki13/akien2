# Step-5：DeepSeek 智能问答（运行说明）

本项目在 Step-5 集成了 DeepSeek API，用于：

- 订餐端：菜品问答 `/order/ask/<dish_id>`
- 管理端：经营顾问 `/manager/advisor`

> 若与其它说明冲突，请以仓库根目录 `CONTRACT.md` 为准。

---

## 1. 必需环境变量

- `DEEPSEEK_API_KEY`（必需）

可选配置：

- `DEEPSEEK_BASE_URL`（默认：`https://api.deepseek.com`）
- `DEEPSEEK_MODEL`（默认：`deepseek-chat`）
- `DEEPSEEK_TIMEOUT_SECONDS`（默认：`30`）

示例（写入 `.env`）：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_MODEL=deepseek-chat
# DEEPSEEK_TIMEOUT_SECONDS=30
```

## 2. Windows（PowerShell）标准启动方式

> 避免 Anaconda / 全局 Python 混用，建议永远用 venv 的 python 执行安装、迁移和启动。

```powershell
# 1) 安装依赖
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 升级数据库（必须）
.\venv\Scripts\python.exe -m flask --app run.py db upgrade

# 3) 启动
.\venv\Scripts\python.exe -m flask --app run.py run --debug
```

常见报错：

- `no such table: restaurants`：通常是没执行 `db upgrade` 或数据库连错位置

---

## 3. 未配置 API Key 时的行为（必须）

当未设置 `DEEPSEEK_API_KEY` 时：

- `/order/ask/<dish_id>` 与 `/manager/advisor` 页面会显示中文提示 **“智能问答功能未配置”**
- 输入框与按钮保持禁用状态
- 页面不崩溃，不抛 500

---

## 4. 相关文件位置

- DeepSeek 封装：`app/ai/deepseek_client.py`
- 订餐端问答：`app/order/routes.py` + `app/templates/order/ask.html`
- 管理端顾问：`app/manager/routes.py` + `app/templates/manager/advisor.html`
