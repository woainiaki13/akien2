# QA引擎 - Windows PowerShell 验证步骤

## 前置条件
- Python 3.9+
- 已有的 Flask 餐厅平台项目
- (可选) DEEPSEEK_API_KEY 环境变量

---

## 步骤 1: 解压并放置文件

```powershell
# 1. 解压新文件到项目目录
Expand-Archive -Path "new_files_qa.zip" -DestinationPath "." -Force

# 2. 解压修改参考文件（仅供参考，需手动合并）
Expand-Archive -Path "modified_existing_files_qa.zip" -DestinationPath "./modification_reference" -Force
```

验证文件结构：
```powershell
# 检查新文件是否存在
Test-Path "app/ai/qa_engine.py"       # 应返回 True
Test-Path "app/ai/qa_prompts.py"      # 应返回 True
Test-Path "app/ai/qa_matcher.py"      # 应返回 True
```

---

## 步骤 2: 手动修改现有文件

### 2.1 修改 `app/ai/__init__.py`

添加以下导入行：
```python
from app.ai import qa_engine
from app.ai import qa_prompts
from app.ai import qa_matcher
```

### 2.2 修改 `app/order/routes.py`

1. 在文件顶部添加导入：
```python
from app.ai import qa_engine
```

2. 找到 `ask(dish_id)` 函数，将 POST 处理部分替换为：
```python
if user_question:
    answer, updated_history = qa_engine.answer_dish_question(
        current_user=current_user,
        dish_id=dish_id,
        question=user_question,
        chat_history=chat_history,
        model_override=None
    )
    save_ai_chat_history(chat_key, updated_history)
    chat_history = updated_history
```

### 2.3 修改 `app/manager/routes.py`

1. 在文件顶部添加导入：
```python
from app.ai import qa_engine
```

2. 找到 `advisor()` 函数，将 POST 处理部分替换为：
```python
if user_question:
    answer, updated_history = qa_engine.answer_manager_question(
        current_user=current_user,
        restaurant_id=restaurant.id,
        question=user_question,
        chat_history=chat_history,
        model_override=None
    )
    save_advisor_chat_history(updated_history)
    chat_history = updated_history
```

---

## 步骤 3: 安装依赖

```powershell
# 激活虚拟环境（如果使用venv）
.\venv\Scripts\Activate.ps1

# 安装依赖（requirements.txt 应已包含所需依赖）
python -m pip install -r requirements.txt

# 验证关键依赖
python -c "import flask; print(f'Flask: {flask.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
```

---

## 步骤 4: 数据库迁移（如需要）

```powershell
# 如果有新的模型更改（本次无需，但保持习惯）
python -m flask --app run.py db upgrade
```

---

## 步骤 5: 设置环境变量（可选）

```powershell
# 临时设置（仅当前会话有效）
$env:DEEPSEEK_API_KEY = "your-api-key-here"
$env:DEEPSEEK_MODEL = "deepseek-chat"

# 或创建 .env 文件（如果项目使用 python-dotenv）
@"
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT_SECONDS=30
"@ | Out-File -FilePath ".env" -Encoding UTF8
```

---

## 步骤 6: 启动开发服务器

```powershell
# 启动 Flask 开发服务器
python -m flask --app run.py run --debug

# 预期输出：
# * Running on http://127.0.0.1:5000
# * Debugger is active!
```

---

## 步骤 7: 功能验证

### 7.1 菜品问答测试

1. 浏览器访问：`http://127.0.0.1:5000/order/ask/<dish_id>`
   - 将 `<dish_id>` 替换为实际的菜品ID（如 `1`）

2. 测试用例：

| 测试场景 | 输入问题 | 预期行为 |
|---------|---------|---------|
| API未配置 | (任意) | 显示警告"智能问答功能未配置" |
| 规则匹配-价格 | "这个多少钱？" | 直接返回价格，无LLM调用 |
| 规则匹配-销量 | "销量怎么样？" | 返回销量统计数据 |
| 规则匹配-购买者 | "谁点过这道菜？" | 返回购买者列表 |
| LLM回答 | "这道菜好吃吗？" | 调用LLM生成回答 |
| 跨菜品查询 | "宫保鸡丁怎么样？" | 自动匹配并回答 |

### 7.2 经营顾问测试

1. 浏览器访问：`http://127.0.0.1:5000/manager/advisor`
   - 需要以餐厅管理员身份登录

2. 测试用例：

| 测试场景 | 输入问题 | 预期行为 |
|---------|---------|---------|
| API未配置 | (任意) | 显示警告"智能问答功能未配置" |
| 规则匹配-VIP | "谁是我的VIP客户？" | 直接返回消费排行 |
| 规则匹配-畅销 | "哪个菜卖得最好？" | 返回销量排行 |
| 规则匹配-营收 | "总共赚了多少钱？" | 返回营收统计 |
| LLM回答 | "如何提高客单价？" | 调用LLM生成建议 |

---

## 步骤 8: 日志检查

```powershell
# 检查是否有Python导入错误
python -c "from app.ai import qa_engine; print('qa_engine loaded OK')"
python -c "from app.ai import qa_prompts; print('qa_prompts loaded OK')"
python -c "from app.ai import qa_matcher; print('qa_matcher loaded OK')"

# 检查规则引擎
python -c "
from app.ai import qa_engine
result = qa_engine.try_rule_answer_manager('谁是VIP', 1)
print(f'Rule match test: {\"PASS\" if result else \"No match (expected if no data)\"}')"
```

---

## 常见问题排查

### 问题1: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'app.ai.qa_engine'
```

**解决**：确认 `app/ai/qa_engine.py` 文件存在，且 `app/ai/__init__.py` 中有正确的导入。

### 问题2: ImportError 循环导入

**解决**：检查 `qa_engine.py` 中的导入顺序，确保 `from app import db` 和模型导入在正确位置。

### 问题3: API调用失败

```
ConnectionError: 无法连接到API服务器
```

**解决**：
1. 检查 `DEEPSEEK_API_KEY` 是否正确设置
2. 检查网络连接
3. 确认 `DEEPSEEK_BASE_URL` 是否正确

### 问题4: Session太大警告

**解决**：聊天历史已自动限制为10轮。如果仍然过大，检查是否有其他session数据，或考虑使用服务端session存储（如Redis）。

---

## 验证清单

- [ ] 新文件已正确放置
- [ ] `app/ai/__init__.py` 已修改
- [ ] `app/order/routes.py` 已修改
- [ ] `app/manager/routes.py` 已修改
- [ ] Flask 服务器正常启动
- [ ] 菜品问答页面可访问
- [ ] 经营顾问页面可访问
- [ ] API未配置时显示正确提示
- [ ] 规则匹配问题能直接返回答案
- [ ] LLM问题能正确调用API

---

## 完成！

如果所有验证步骤通过，QA引擎已成功集成到您的Flask餐厅平台中。
