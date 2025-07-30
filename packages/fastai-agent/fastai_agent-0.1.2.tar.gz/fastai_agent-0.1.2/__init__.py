"""
Fastai Agent - 一个基于 FastAPI 和 LangGraph 的智能代理框架
"""

__version__ = "0.1.2"
__author__ = "jackjack"
__email__ = "your.email@example.com"

from .agent import Fastai
from .models import Model, Meta, Schema
from .schemas import SchemaMeta
from .utils import Int, Char, Text, Json, Datetime, FK, M2M
from .dotenv import DotEnv, env

__all__ = [
    "Fastai",
    "Model",
    "Meta",
    "Schema",
    "SchemaMeta",
    "Int",
    "Char",
    "Text",
    "Json",
    "Datetime",
    "FK",
    "M2M",
    "DotEnv",
    "env",
] 