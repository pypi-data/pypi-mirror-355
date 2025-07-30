import asyncio
from tortoise import Tortoise
from .models import Model
from .utils import Int, Char, Text, Json, Datetime, FK, M2M
from .agent import Fastai

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

async def init_db():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['fastai_agent.main']}
    )
    await Tortoise.generate_schemas()

async def main():
    # 初始化数据库
    await init_db()
    
    # 创建 Fastai 实例
    agent = Fastai([Project, Context])
    
    # 示例查询
    queries = [
        "创建一个名为'测试项目'的项目",
        "查询所有项目",
        "更新ID为1的项目名称为'新项目名称'",
        "删除ID为1的项目"
    ]
    
    for query in queries:
        print(f"\n📝 用户查询: {query}")
        result = await agent.run(query)
        print(f"📊 结果: {result}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 