# MANIFEST_step5.md（Step-5 文件清单）

本清单描述 Step-5（DeepSeek 智能问答）集成涉及的关键文件与职责。

> 若与其它说明冲突，以 `CONTRACT.md` 为准。

---

## 1. 代码文件

- `app/ai/deepseek_client.py`
  - DeepSeek API 的 requests 封装
  - 负责读取环境变量：`DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` / `DEEPSEEK_TIMEOUT_SECONDS`
  - 提供 `is_api_configured()` 与 `call_chat_completion()`

- `app/order/routes.py`
  - 路由 `/order/ask/<dish_id>`：菜品问答（真实调用 DeepSeek）
  - 未配置 Key 时：提示“智能问答功能未配置”，并确保页面不崩溃

- `app/manager/routes.py`
  - 路由 `/manager/advisor`：经营顾问（真实调用 DeepSeek）
  - 未配置 Key 时：提示“智能问答功能未配置”，并确保页面不崩溃

---

## 2. 模板文件

- `app/templates/order/ask.html`
  - 菜品问答页面
  - 未配置 Key 时：显示“智能问答功能未配置”，并禁用表单

- `app/templates/manager/advisor.html`
  - 经营顾问页面
  - 未配置 Key 时：显示“智能问答功能未配置”，并禁用表单

---

## 3. 配置与文档

- `.env.example`
  - 补充 Step-5 相关环境变量示例

- `README_step5_zh.md`
  - Step-5 运行说明、Windows 启动命令、未配置 Key 时的行为说明
