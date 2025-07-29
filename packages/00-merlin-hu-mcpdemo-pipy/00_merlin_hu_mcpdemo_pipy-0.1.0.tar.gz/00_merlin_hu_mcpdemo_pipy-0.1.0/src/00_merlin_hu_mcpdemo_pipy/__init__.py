# 前面的写法固定
# server.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
# @mcp.tool()是python的装饰器，用来给下面的行数增加功能，在这里表标识下述的函数是一个MCP工具
# 类似于"""Add two numbers"""的注释是必须要写的，是用自然语言告诉LLM这个函数的功能是什么
# a: int, b: int 中的: int类型修饰符是必须的，帮助大模型理解传参的类型
# @mcp.tool()声明为一个工具，类似于Http Rest API里面的post方法
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# LLM调用工具通常会产生附加作用，例如发邮件修改文件等
# 此处常resource类似于Http Rest API里面的get方法
# 通为大模型提供只读数据
# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
    
# 运行的时候可以再加两行类似如下，指定mcp运行于STDIO协议，为一个独立运行的程序

def main() -> None:
    mcp.run(transport="stdio")
