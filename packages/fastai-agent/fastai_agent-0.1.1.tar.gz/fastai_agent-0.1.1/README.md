# Fastai Agent

基于 Tortoise ORM、FastAPI、Pydantic、LangChain 的智能数据库/接口自动化 Agent 框架。

## 特性

- 🎯 自然语言处理数据库操作
- 🔄 自动生成 CRUD 接口
- 📝 智能上下文管理
- 🔍 自动字段类型推断
- 🛡️ 完整的错误处理
- 📚 丰富的文档支持

## 安装

```bash
pip install fastai-agent
```

## 快速开始

### 1. 定义模型

```python
from fastai_agent import Model, Int, Char, Text, Json, Datetime, FK

class Project(Model):
    """项目模型，用于管理项目信息"""
    id = Int(pk=True)
    name = Char(max_length=100)
    description = Text()
    created_at = Datetime(auto_now_add=True)
    updated_at = Datetime(auto_now=True)

class Context(Model):
    """上下文模型，用于存储对话上下文"""
    id = Int(pk=True)
    project = FK(Project)
    content = Json()
    created_at = Datetime(auto_now_add=True)
```

### 2. 初始化 Agent

```python
from fastai_agent import Fastai
from tortoise import Tortoise

async def init_db():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['your_module']}
    )
    await Tortoise.generate_schemas()

# 初始化数据库
await init_db()

# 创建 Fastai 实例
agent = Fastai([Project, Context])
```

### 3. 使用自然语言查询

```python
# 创建项目
result = await agent.run("创建一个名为'测试项目'的项目")
print(result)

# 查询项目
result = await agent.run("查询所有项目")
print(result)

# 更新项目
result = await agent.run("更新ID为1的项目名称为'新项目名称'")
print(result)

# 删除项目
result = await agent.run("删除ID为1的项目")
print(result)
```

### 4. 使用 FastAPI 集成

```python
from fastapi import FastAPI
from fastai_agent import Fastai

app = FastAPI()
agent = Fastai([Project, Context])

@app.post("/query")
async def query(query: str):
    result = await agent.run(query)
    return {"result": result}
```

## 字段类型

- `Int`: 整数字段
- `Char`: 字符串字段（带最大长度限制）
- `Text`: 文本字段
- `Json`: JSON 字段
- `Datetime`: 日期时间字段
- `FK`: 外键关系
- `M2M`: 多对多关系

## 开发

### 环境设置

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/fastai-agent.git
cd fastai-agent
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

## 贡献

欢迎提交 Pull Request 和 Issue！

## 许可证

MIT License 